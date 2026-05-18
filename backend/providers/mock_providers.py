from __future__ import annotations

from pathlib import Path
import re

from image.anchor_generator import generate_anchor_ref_image
from image.panel_generator import generate_entity_appearance_ref, generate_panel_image
from pipeline.reference_selector import select_references
from pipeline.revision_planner import MockRevisionPlanner
from pipeline.storyboard_planner import MockStoryboardPlanner
from providers.image_base import ImageProvider
from providers.llm_base import LLMProvider
from providers.segment_base import SegmentProvider


class MockLLMProvider(LLMProvider):
    provider_name = "mock_llm"

    def __init__(self) -> None:
        self.storyboard_planner = MockStoryboardPlanner()
        self.revision_planner = MockRevisionPlanner()

    def generate_storyboard(
        self,
        user_prompt: str,
        layout: str,
        style: str,
        panel_count: int,
        style_prompt: str,
    ) -> dict:
        return self.storyboard_planner.plan(user_prompt, layout, style)

    def select_references(
        self,
        panel: dict,
        entities: list[dict],
        entity_pool_summary: dict,
    ) -> dict:
        mock_pool = {
            entity_id: {"refs": refs}
            for entity_id, refs in entity_pool_summary.items()
        }
        refs_by_entity = select_references(mock_pool, panel["entities_used"])
        return {
            "selected_refs": {
                entity_id: [ref["ref_id"] for ref in refs]
                for entity_id, refs in refs_by_entity.items()
            }
        }

    def plan_revision(
        self,
        storyboard: dict,
        feedback: str,
        revision_type: str,
        panel_id: int | None = None,
    ) -> dict:
        if revision_type == "panel":
            if panel_id is None:
                raise ValueError("panel_id is required for panel revision")
            return self.revision_planner.plan_panel(storyboard, panel_id, feedback)
        return self.revision_planner.plan_global(storyboard, feedback)

    def generate_ref_note(self, panel_summary: str, entity: dict) -> str:
        return f"appearance from panel: {panel_summary[:72]}"


class MockImageProvider(ImageProvider):
    provider_name = "mock_image"

    def generate_anchor_image(
        self,
        entity_id: str,
        description: str,
        style_prompt: str,
        output_path: Path,
    ) -> None:
        generate_anchor_ref_image(output_path, entity_id, description, f"{entity_id}_anchor")

    def generate_panel_image(
        self,
        panel_prompt: str,
        reference_sheet_path: Path,
        output_path: Path,
    ) -> None:
        panel_id = _panel_id_from_path(output_path)
        summary = _extract_current_panel(panel_prompt)
        entities_used = _extract_entities(panel_prompt)
        generate_panel_image(
            path=output_path,
            panel_id=panel_id,
            summary=summary,
            style="mock",
            entities_used=entities_used,
            selected_refs={entity_id: [] for entity_id in entities_used},
        )


class MockSegmentProvider(SegmentProvider):
    provider_name = "mock_segment"

    def segment_entity(
        self,
        image_path: Path,
        entity_id: str,
        description: str,
        output_path: Path,
    ) -> None:
        ref_id = output_path.stem
        source = "anchor" if "anchor" in image_path.stem else image_path.stem
        note = f"mock cutout for {source}"
        generate_entity_appearance_ref(output_path, entity_id, ref_id, source, note)


def _panel_id_from_path(path: Path) -> int:
    match = re.search(r"panel_(\d+)", path.stem)
    return int(match.group(1)) if match else 1


def _extract_current_panel(panel_prompt: str) -> str:
    marker = "Current panel:"
    if marker not in panel_prompt:
        return panel_prompt[:180]
    after = panel_prompt.split(marker, 1)[1]
    requirements = after.split("Requirements:", 1)[0]
    return " ".join(requirements.split())[:360]


def _extract_entities(panel_prompt: str) -> list[str]:
    marker = "Entities in this panel:"
    if marker not in panel_prompt:
        return ["entity"]
    block = panel_prompt.split(marker, 1)[1].split("Current panel:", 1)[0]
    entities = []
    for line in block.splitlines():
        cleaned = line.strip().lstrip("-").strip()
        if ":" in cleaned:
            entities.append(cleaned.split(":", 1)[0].strip())
    return entities or ["entity"]
