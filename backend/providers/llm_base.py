from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    provider_name = "llm"

    @abstractmethod
    def generate_storyboard(
        self,
        user_prompt: str,
        layout: str,
        style: str,
        panel_count: int,
        style_prompt: str,
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    def select_references(
        self,
        panel: dict,
        entities: list[dict],
        entity_pool_summary: dict,
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    def plan_revision(
        self,
        storyboard: dict,
        feedback: str,
        revision_type: str,
        panel_id: int | None = None,
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    def generate_ref_note(self, panel_summary: str, entity: dict) -> str:
        raise NotImplementedError
