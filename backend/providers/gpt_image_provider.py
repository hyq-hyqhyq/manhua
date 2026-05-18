import base64
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx

from config import settings
from providers.errors import ProviderError, ProviderUnavailableError
from providers.image_base import ImageProvider


class GPTImageProvider(ImageProvider):
    provider_name = "gpt_image"

    def __init__(self) -> None:
        self.api_key = settings.openai_image_api_key
        self.base_url = (
            settings.openai_image_base_url or settings.openai_base_url
        ).rstrip("/")
        self.image_base_url = settings.openai_image_base_url.rstrip("/")
        self.model = settings.openai_image_model
        self.endpoint = settings.openai_image_endpoint.rstrip("/")
        self.edits_endpoint = settings.openai_image_edits_endpoint.rstrip("/")
        self.generations_endpoint = settings.openai_image_generations_endpoint.rstrip("/")
        self.timeout_seconds = settings.openai_image_timeout_seconds

    def generate_anchor_image(
        self,
        entity_id: str,
        description: str,
        style_prompt: str,
        output_path: Path,
    ) -> None:
        self._ensure_configured()
        prompt = (
            "Create a clean isolated character/object anchor image for a comic Entity Pool.\n\n"
            f"Entity id: {entity_id}\n"
            f"Description: {description}\n"
            f"Style: {style_prompt}\n\n"
            "Requirements:\n"
            "- Show only this entity.\n"
            "- Use a simple light background.\n"
            "- Make the silhouette clear for later segmentation.\n"
            "- Do not include readable text."
        )
        payload = {
            "model": self.model,
            "prompt": prompt,
            "size": "1024x1024",
        }
        data = self._post_json(self._image_url("generations"), payload)
        self._write_image_response(data, output_path)

    def generate_panel_image(
        self,
        panel_prompt: str,
        reference_sheet_path: Path,
        output_path: Path,
    ) -> None:
        self._ensure_configured()
        if not reference_sheet_path.exists():
            raise ProviderError(f"Missing reference sheet: {reference_sheet_path}")

        url = self._image_url("edits")
        headers = {"Authorization": f"Bearer {self.api_key}"}
        files = {
            "image": (
                reference_sheet_path.name,
                reference_sheet_path.read_bytes(),
                "image/png",
            )
        }
        data = {
            "model": self.model,
            "prompt": panel_prompt,
            "size": "1024x1024",
        }

        try:
            response = httpx.post(
                url,
                headers=headers,
                data=data,
                files=files,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            self._write_image_response(response.json(), output_path)
        except Exception as error:
            raise ProviderError(f"GPT Image panel generation failed: {error}") from error

    def _ensure_configured(self) -> None:
        missing = []
        if not self.api_key:
            missing.append("OPENAI_IMAGE_API_KEY")
        if not (self.base_url or self.image_base_url or self.endpoint):
            missing.append("OPENAI_BASE_URL or OPENAI_IMAGE_BASE_URL")
        if not self.model:
            missing.append("OPENAI_IMAGE_MODEL")
        if missing:
            raise ProviderUnavailableError(
                f"GPT Image provider is not configured: missing {', '.join(missing)}"
            )

    def _image_url(self, operation: str) -> str:
        endpoint = self._operation_endpoint(operation)
        if endpoint:
            return self._absolute_url(endpoint)

        base_url = self.image_base_url or self._derive_image_base_url()
        if not base_url:
            raise ProviderUnavailableError("Image base URL is not configured")

        base_url = self._absolute_url(base_url)
        if base_url.endswith(f"/images/{operation}"):
            return base_url
        if base_url.endswith("/images"):
            return f"{base_url}/{operation}"
        if base_url.endswith("/v1"):
            return f"{base_url}/images/{operation}"
        return f"{base_url}/v1/images/{operation}"

    def _operation_endpoint(self, operation: str) -> str:
        if operation == "edits" and self.edits_endpoint:
            return self.edits_endpoint
        if operation == "generations" and self.generations_endpoint:
            return self.generations_endpoint
        if self.endpoint and self.endpoint.endswith(operation):
            return self.endpoint
        return ""

    def _derive_image_base_url(self) -> str:
        for candidate in (self.endpoint, self.base_url):
            if not candidate:
                continue
            if "/v1/" in candidate:
                return candidate.split("/v1/", 1)[0].rstrip("/") + "/v1"
            if candidate.endswith("/v1"):
                return candidate
        return self.base_url

    def _absolute_url(self, url: str) -> str:
        if url.startswith("http://") or url.startswith("https://"):
            return url.rstrip("/")
        if not url.startswith("/"):
            return url.rstrip("/")

        base = self.image_base_url or self._derive_image_base_url()
        parsed = urlparse(base)
        if not parsed.scheme or not parsed.netloc:
            raise ProviderUnavailableError(
                f"Relative image endpoint {url} requires OPENAI_IMAGE_BASE_URL or OPENAI_BASE_URL with host"
            )
        return f"{parsed.scheme}://{parsed.netloc}{url}".rstrip("/")

    def _post_json(self, url: str, payload: dict[str, Any]) -> dict:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        try:
            response = httpx.post(
                url,
                headers=headers,
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            return response.json()
        except Exception as error:
            raise ProviderError(f"GPT Image request failed: {error}") from error

    def _write_image_response(self, data: dict[str, Any], output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image_item = (data.get("data") or [{}])[0]

        if image_item.get("b64_json"):
            output_path.write_bytes(base64.b64decode(image_item["b64_json"]))
            return

        if data.get("b64_json"):
            output_path.write_bytes(base64.b64decode(data["b64_json"]))
            return

        image_url = image_item.get("url") or data.get("url")
        if image_url:
            try:
                response = httpx.get(image_url, timeout=self.timeout_seconds)
                response.raise_for_status()
                output_path.write_bytes(response.content)
                return
            except Exception as error:
                raise ProviderError(f"Failed to download generated image: {error}") from error

        raise ProviderError("GPT Image response did not include b64_json or url")
