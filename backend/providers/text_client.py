from typing import Any

import httpx

from providers.errors import ProviderError, ProviderUnavailableError
from providers.json_utils import parse_json_object


class OpenAICompatibleTextClient:
    def __init__(
        self,
        provider_name: str,
        api_key: str,
        base_url: str,
        model: str,
        timeout_seconds: float,
    ) -> None:
        self.provider_name = provider_name
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def complete_text(self, system_prompt: str, user_prompt: str) -> str:
        self._ensure_configured()
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = httpx.post(
                self._chat_url(),
                headers=headers,
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
            return self._extract_message(data)
        except Exception as error:
            raise ProviderError(f"{self.provider_name} text request failed: {error}") from error

    def complete_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        text = self.complete_text(system_prompt, user_prompt)
        try:
            return parse_json_object(text)
        except Exception as error:
            raise ProviderError(f"{self.provider_name} returned invalid JSON: {error}") from error

    def _ensure_configured(self) -> None:
        missing = []
        if not self.api_key:
            missing.append("API key")
        if not self.base_url:
            missing.append("base URL")
        if not self.model:
            missing.append("model")
        if missing:
            raise ProviderUnavailableError(
                f"{self.provider_name} is not configured: missing {', '.join(missing)}"
            )

    def _chat_url(self) -> str:
        if self.base_url.endswith("/chat/completions"):
            return self.base_url
        if self.base_url.endswith("/v1"):
            return f"{self.base_url}/chat/completions"
        return f"{self.base_url}/v1/chat/completions"

    def _extract_message(self, data: dict[str, Any]) -> str:
        try:
            choice = data["choices"][0]
            if "message" in choice:
                content = choice["message"].get("content", "")
            else:
                content = choice.get("text", "")
            if isinstance(content, list):
                parts = []
                for item in content:
                    if isinstance(item, dict) and "text" in item:
                        parts.append(item["text"])
                    elif isinstance(item, str):
                        parts.append(item)
                content = "\n".join(parts)
            if not content:
                raise KeyError("empty content")
            return str(content)
        except Exception as error:
            raise ProviderError(
                f"{self.provider_name} response did not contain message content"
            ) from error
