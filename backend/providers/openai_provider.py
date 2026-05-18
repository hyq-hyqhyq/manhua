from __future__ import annotations

from config import settings
from pipeline.prompt_builder import (
    JSON_SYSTEM_PROMPT,
    ref_note_prompt,
    reference_selection_prompt,
    revision_prompt,
    storyboard_prompt,
)
from providers.llm_base import LLMProvider
from providers.text_client import OpenAICompatibleTextClient


class OpenAIProvider(LLMProvider):
    provider_name = "openai_text"

    def __init__(self) -> None:
        self.client = OpenAICompatibleTextClient(
            provider_name=self.provider_name,
            api_key=settings.openai_text_api_key,
            base_url=settings.openai_text_base_url,
            model=settings.openai_text_model,
            timeout_seconds=settings.request_timeout_seconds,
        )

    def generate_storyboard(
        self,
        user_prompt: str,
        layout: str,
        style: str,
        panel_count: int,
        style_prompt: str,
    ) -> dict:
        return self.client.complete_json(
            JSON_SYSTEM_PROMPT,
            storyboard_prompt(user_prompt, layout, style, panel_count, style_prompt),
        )

    def select_references(
        self,
        panel: dict,
        entities: list[dict],
        entity_pool_summary: dict,
    ) -> dict:
        return self.client.complete_json(
            JSON_SYSTEM_PROMPT,
            reference_selection_prompt(panel, entities, entity_pool_summary),
        )

    def plan_revision(
        self,
        storyboard: dict,
        feedback: str,
        revision_type: str,
        panel_id: int | None = None,
    ) -> dict:
        return self.client.complete_json(
            JSON_SYSTEM_PROMPT,
            revision_prompt(storyboard, feedback, revision_type, panel_id),
        )

    def generate_ref_note(self, panel_summary: str, entity: dict) -> str:
        return self.client.complete_text(
            "Return a concise visual note only.",
            ref_note_prompt(panel_summary, entity),
        ).strip().strip('"')
