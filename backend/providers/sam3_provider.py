import base64
import shutil
from pathlib import Path
from typing import Any

import httpx

from config import settings
from providers.errors import ProviderError, ProviderUnavailableError
from providers.segment_base import SegmentProvider


class SAM3Provider(SegmentProvider):
    provider_name = "sam3"

    def __init__(self) -> None:
        self.endpoint = settings.sam3_endpoint.rstrip("/")
        self.timeout_seconds = settings.request_timeout_seconds

    def segment_entity(
        self,
        image_path: Path,
        entity_id: str,
        description: str,
        output_path: Path,
    ) -> None:
        if not self.endpoint:
            raise ProviderUnavailableError("SAM3 endpoint is not configured")
        if not image_path.exists():
            raise ProviderError(f"Missing image for SAM3 segmentation: {image_path}")

        files = {
            "image": (
                image_path.name,
                image_path.read_bytes(),
                "image/png",
            )
        }
        data = {
            "entity_id": entity_id,
            "description": description,
        }

        try:
            response = httpx.post(
                self.endpoint,
                data=data,
                files=files,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            self._write_segmentation_response(response, output_path)
        except Exception as error:
            raise ProviderError(f"SAM3 segmentation failed for {entity_id}: {error}") from error

    def _write_segmentation_response(self, response: httpx.Response, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        content_type = response.headers.get("content-type", "")

        if content_type.startswith("image/"):
            output_path.write_bytes(response.content)
            return

        payload = response.json()
        self._write_json_payload(payload, output_path)

    def _write_json_payload(self, payload: dict[str, Any], output_path: Path) -> None:
        b64_value = (
            payload.get("rgba_base64")
            or payload.get("image_base64")
            or payload.get("b64_json")
        )
        if b64_value:
            output_path.write_bytes(base64.b64decode(b64_value))
            return

        url = payload.get("rgba_url") or payload.get("image_url") or payload.get("url")
        if url:
            response = httpx.get(url, timeout=self.timeout_seconds)
            response.raise_for_status()
            output_path.write_bytes(response.content)
            return

        rgba_path = payload.get("rgba_path") or payload.get("path")
        if rgba_path:
            source = Path(rgba_path)
            if not source.exists():
                raise ProviderError(f"SAM3 returned missing local path: {rgba_path}")
            shutil.copyfile(source, output_path)
            return

        raise ProviderError("SAM3 response did not include image bytes, base64, url, or path")
