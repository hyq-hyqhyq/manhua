from __future__ import annotations

from pathlib import Path

from config import settings
from pipeline.prompt_builder import panel_image_prompt
from pipeline.reference_selector import select_references
from pipeline.validators import (
    refs_from_selected_ids,
    validate_panel_text,
    validate_reference_selection,
    validate_revision_plan,
    validate_storyboard,
)
from pool.entity_pool import append_ref, create_entity_pool, next_ref_id
from pool.reference_sheet import generate_reference_sheet
from providers.errors import ProviderError
from providers.gpt_image_provider import GPTImageProvider
from providers.mock_providers import MockImageProvider, MockLLMProvider, MockSegmentProvider
from providers.openai_provider import OpenAIProvider
from providers.sam3_provider import SAM3Provider
from render.stitcher import stitch_panels
from storage.file_store import FileStore


class ComicPipeline:
    def __init__(self) -> None:
        self.store = FileStore(settings.outputs_dir, settings.static_outputs_prefix)
        self.mock_llm = MockLLMProvider()
        self.mock_image_provider = MockImageProvider()
        self.mock_segment_provider = MockSegmentProvider()
        self.openai_provider = OpenAIProvider()
        self.gpt_image_provider = GPTImageProvider()
        self.sam3_provider = SAM3Provider()

    def create_comic(self, user_prompt: str, layout: str, style: str) -> dict[str, str]:
        comic_id = self.store.create_comic_id()
        comic_dir = self.store.init_comic_dir(comic_id)
        total_panels = settings.layouts[layout]["panel_count"]

        try:
            self._write_status(
                comic_id,
                "running",
                0,
                total_panels,
                "Planning storyboard",
                provider_status=self._initial_provider_status(),
            )
            storyboard = self._generate_storyboard(comic_id, user_prompt, layout, style)
            self.store.save_json(comic_dir / "storyboard.json", storyboard)

            entity_pool = self._initialize_entity_pool(comic_id, comic_dir, storyboard)
            self.store.save_json(comic_dir / "entity_pool.json", entity_pool)

            for panel in storyboard["panels"]:
                self._write_status(
                    comic_id,
                    "running",
                    panel["panel_id"],
                    total_panels,
                    f"Generating panel {panel['panel_id']}",
                )
                self._generate_panel_assets(comic_id, comic_dir, storyboard, entity_pool, panel)
                self.store.save_json(comic_dir / "entity_pool.json", entity_pool)

            self._stitch_comic(comic_dir, storyboard)
            self._write_status(comic_id, "completed", total_panels, total_panels, "Completed")
            return {"comic_id": comic_id, "status": "completed"}
        except Exception as error:
            self._write_status(comic_id, "failed", 0, total_panels, str(error))
            raise

    def get_status(self, comic_id: str) -> dict:
        comic_dir = self.store.require_comic_dir(comic_id)
        return self.store.load_json(comic_dir / "status.json")

    def get_comic(self, comic_id: str) -> dict:
        comic_dir = self.store.require_comic_dir(comic_id)
        storyboard = self.store.load_json(comic_dir / "storyboard.json")
        entity_pool = self.store.load_json(comic_dir / "entity_pool.json")
        status = self.get_status(comic_id)

        panels = []
        for panel in storyboard["panels"]:
            panel_id = panel["panel_id"]
            panels.append(
                {
                    "panel_id": panel_id,
                    "image_path": self.store.to_public_path(
                        comic_dir / "panels" / f"panel_{panel_id}.png"
                    ),
                    "summary": panel["summary"],
                    "text": panel.get("text", []),
                    "reference_sheet_path": self.store.to_public_path(
                        comic_dir / "reference_sheets" / f"panel_{panel_id}_refsheet.png"
                    ),
                }
            )

        return {
            "comic_id": comic_id,
            "status": status["status"],
            "storyboard": storyboard,
            "comic_page": self.store.to_public_path(comic_dir / "final_comic.png"),
            "panels": panels,
            "entity_pool": entity_pool,
            "warnings": status.get("warnings", []),
            "provider_status": status.get("provider_status", self._initial_provider_status()),
        }

    def revise_global(self, comic_id: str, feedback: str) -> dict:
        comic_dir = self.store.require_comic_dir(comic_id)
        storyboard = self.store.load_json(comic_dir / "storyboard.json")
        entity_pool = self.store.load_json(comic_dir / "entity_pool.json")
        revision_plan = self._plan_revision(comic_id, storyboard, feedback, "global")
        return self._apply_revision(comic_id, comic_dir, storyboard, entity_pool, revision_plan)

    def revise_panel(
        self,
        comic_id: str,
        panel_id: int,
        feedback: str,
        summary: str | None = None,
        text: list[dict] | None = None,
    ) -> dict:
        comic_dir = self.store.require_comic_dir(comic_id)
        storyboard = self.store.load_json(comic_dir / "storyboard.json")
        entity_pool = self.store.load_json(comic_dir / "entity_pool.json")
        if summary is not None or text is not None:
            revision_plan = self._direct_panel_revision(storyboard, panel_id, summary, text)
        else:
            revision_plan = self._plan_revision(comic_id, storyboard, feedback, "panel", panel_id)
        return self._apply_revision(comic_id, comic_dir, storyboard, entity_pool, revision_plan)

    def _generate_storyboard(
        self,
        comic_id: str,
        user_prompt: str,
        layout: str,
        style: str,
    ) -> dict:
        panel_count = settings.layouts[layout]["panel_count"]
        style_prompt = self._style_prompt(style)

        if settings.use_mock_providers:
            self._mark_provider(comic_id, "storyboard_llm", self.mock_llm.provider_name)
            return validate_storyboard(
                self.mock_llm.generate_storyboard(user_prompt, layout, style, panel_count, style_prompt),
                layout,
                style,
                panel_count,
            )

        try:
            storyboard = self.openai_provider.generate_storyboard(
                user_prompt,
                layout,
                style,
                panel_count,
                style_prompt,
            )
            storyboard = validate_storyboard(storyboard, layout, style, panel_count)
            self._mark_provider(comic_id, "storyboard_llm", self.openai_provider.provider_name)
            return storyboard
        except Exception as error:
            self._append_warning(comic_id, f"OpenAI text storyboard failed; using mock fallback. {error}")

        if not settings.allow_mock_text_fallback:
            raise ProviderError("Storyboard generation failed and mock text fallback is disabled")

        self._mark_provider(comic_id, "storyboard_llm", self.mock_llm.provider_name)
        return validate_storyboard(
            self.mock_llm.generate_storyboard(user_prompt, layout, style, panel_count, style_prompt),
            layout,
            style,
            panel_count,
        )

    def _initialize_entity_pool(self, comic_id: str, comic_dir: Path, storyboard: dict) -> dict:
        entity_pool = create_entity_pool(storyboard["entities"])
        style_prompt = self._style_prompt(storyboard["style"])

        for entity in storyboard["entities"]:
            entity_id = entity["entity_id"]
            anchor_path = comic_dir / "anchors" / f"{entity_id}_anchor.png"
            self._generate_anchor_image(comic_id, entity, style_prompt, anchor_path)

            ref_id = next_ref_id(entity_pool, entity_id)
            rgba_path = comic_dir / "entity_pool" / entity_id / f"{ref_id}.png"
            self._segment_entity(comic_id, anchor_path, entity, rgba_path)
            append_ref(
                entity_pool,
                entity_id,
                self.store.to_public_path(rgba_path),
                "anchor",
                "anchor appearance",
            )

        return entity_pool

    def _generate_panel_assets(
        self,
        comic_id: str,
        comic_dir: Path,
        storyboard: dict,
        entity_pool: dict,
        panel: dict,
    ) -> None:
        panel_id = panel["panel_id"]
        selected_refs = self._select_references(comic_id, storyboard, entity_pool, panel)
        refsheet_path = comic_dir / "reference_sheets" / f"panel_{panel_id}_refsheet.png"
        panel_path = comic_dir / "panels" / f"panel_{panel_id}.png"

        generate_reference_sheet(
            refsheet_path,
            panel_id,
            selected_refs,
            self.store.public_to_disk_path,
        )

        entities_by_id = {
            entity["entity_id"]: entity
            for entity in storyboard["entities"]
        }
        entities_used = [
            entities_by_id[entity_id]
            for entity_id in panel["entities_used"]
            if entity_id in entities_by_id
        ]
        panel_prompt = panel_image_prompt(
            panel,
            self._style_prompt(storyboard["style"]),
            entities_used,
        )
        self._generate_panel_image(comic_id, panel_prompt, refsheet_path, panel_path)

        for entity_id in panel["entities_used"]:
            entity = entities_by_id[entity_id]
            ref_id = next_ref_id(entity_pool, entity_id)
            ref_path = comic_dir / "entity_pool" / entity_id / f"{ref_id}.png"
            self._segment_entity(comic_id, panel_path, entity, ref_path)
            note = self._generate_ref_note(comic_id, panel, entity)
            append_ref(
                entity_pool,
                entity_id,
                self.store.to_public_path(ref_path),
                f"panel_{panel_id}",
                note,
            )

    def _select_references(
        self,
        comic_id: str,
        storyboard: dict,
        entity_pool: dict,
        panel: dict,
    ) -> dict[str, list[dict]]:
        if settings.use_mock_providers:
            self._mark_provider(comic_id, "reference_selector", self.mock_llm.provider_name)
            return select_references(entity_pool, panel["entities_used"])

        entities_by_id = {
            entity["entity_id"]: entity
            for entity in storyboard["entities"]
        }
        current_entities = [
            entities_by_id[entity_id]
            for entity_id in panel["entities_used"]
            if entity_id in entities_by_id
        ]
        entity_pool_summary = self._entity_pool_summary(entity_pool, panel["entities_used"])

        for provider in self._text_providers():
            try:
                selection = provider.select_references(panel, current_entities, entity_pool_summary)
                selected_ids = validate_reference_selection(selection, panel, entity_pool)
                self._mark_provider(comic_id, "reference_selector", provider.provider_name)
                return refs_from_selected_ids(entity_pool, selected_ids)
            except Exception as error:
                self._append_warning(
                    comic_id,
                    f"{provider.provider_name} reference selection failed; trying fallback. {error}",
                )

        self._mark_provider(comic_id, "reference_selector", self.mock_llm.provider_name)
        return select_references(entity_pool, panel["entities_used"])

    def _plan_revision(
        self,
        comic_id: str,
        storyboard: dict,
        feedback: str,
        revision_type: str,
        panel_id: int | None = None,
    ) -> dict:
        if settings.use_mock_providers:
            self._mark_provider(comic_id, "revision_planner", self.mock_llm.provider_name)
            return validate_revision_plan(
                self.mock_llm.plan_revision(storyboard, feedback, revision_type, panel_id),
                storyboard,
                revision_type,
                panel_id,
            )

        for provider in self._text_providers():
            try:
                revision_plan = provider.plan_revision(storyboard, feedback, revision_type, panel_id)
                revision_plan = validate_revision_plan(
                    revision_plan,
                    storyboard,
                    revision_type,
                    panel_id,
                )
                self._mark_provider(comic_id, "revision_planner", provider.provider_name)
                return revision_plan
            except Exception as error:
                self._append_warning(
                    comic_id,
                    f"{provider.provider_name} revision planning failed; trying fallback. {error}",
                )

        if not settings.allow_mock_text_fallback:
            raise ProviderError("Revision planning failed and mock text fallback is disabled")

        self._mark_provider(comic_id, "revision_planner", self.mock_llm.provider_name)
        return validate_revision_plan(
            self.mock_llm.plan_revision(storyboard, feedback, revision_type, panel_id),
            storyboard,
            revision_type,
            panel_id,
        )

    def _generate_ref_note(self, comic_id: str, panel: dict, entity: dict) -> str:
        fallback_note = f"appearance from panel_{panel['panel_id']}"
        if settings.use_mock_providers:
            self._mark_provider(comic_id, "ref_note_llm", self.mock_llm.provider_name)
            return fallback_note

        for provider in self._text_providers():
            try:
                note = provider.generate_ref_note(panel["summary"], entity)
                note = " ".join(note.split())[:96]
                if note:
                    self._mark_provider(comic_id, "ref_note_llm", provider.provider_name)
                    return note
            except Exception as error:
                self._append_warning(
                    comic_id,
                    f"{provider.provider_name} ref note failed; trying fallback. {error}",
                )

        self._mark_provider(comic_id, "ref_note_llm", self.mock_llm.provider_name)
        return fallback_note

    def _generate_anchor_image(
        self,
        comic_id: str,
        entity: dict,
        style_prompt: str,
        output_path: Path,
    ) -> None:
        if settings.use_mock_providers:
            self.mock_image_provider.generate_anchor_image(
                entity["entity_id"],
                entity["description"],
                style_prompt,
                output_path,
            )
            self._mark_provider(comic_id, "image", self.mock_image_provider.provider_name)
            return

        try:
            self.gpt_image_provider.generate_anchor_image(
                entity["entity_id"],
                entity["description"],
                style_prompt,
                output_path,
            )
            self._mark_provider(comic_id, "image", self.gpt_image_provider.provider_name)
        except Exception as error:
            if not settings.allow_mock_image_fallback:
                raise ProviderError(f"GPT Image anchor generation failed: {error}") from error
            self._append_warning(comic_id, f"GPT Image anchor failed; using mock image fallback. {error}")
            self.mock_image_provider.generate_anchor_image(
                entity["entity_id"],
                entity["description"],
                style_prompt,
                output_path,
            )
            self._mark_provider(
                comic_id,
                "image",
                f"{self.gpt_image_provider.provider_name}+{self.mock_image_provider.provider_name}",
            )

    def _generate_panel_image(
        self,
        comic_id: str,
        panel_prompt: str,
        reference_sheet_path: Path,
        output_path: Path,
    ) -> None:
        if settings.use_mock_providers:
            self.mock_image_provider.generate_panel_image(panel_prompt, reference_sheet_path, output_path)
            self._mark_provider(comic_id, "image", self.mock_image_provider.provider_name)
            return

        try:
            self.gpt_image_provider.generate_panel_image(panel_prompt, reference_sheet_path, output_path)
            self._mark_provider(comic_id, "image", self.gpt_image_provider.provider_name)
        except Exception as error:
            if not settings.allow_mock_image_fallback:
                raise ProviderError(f"GPT Image panel generation failed: {error}") from error
            self._append_warning(comic_id, f"GPT Image panel failed; using mock image fallback. {error}")
            self.mock_image_provider.generate_panel_image(panel_prompt, reference_sheet_path, output_path)
            self._mark_provider(
                comic_id,
                "image",
                f"{self.gpt_image_provider.provider_name}+{self.mock_image_provider.provider_name}",
            )

    def _segment_entity(
        self,
        comic_id: str,
        image_path: Path,
        entity: dict,
        output_path: Path,
    ) -> None:
        if settings.use_mock_providers:
            self.mock_segment_provider.segment_entity(
                image_path,
                entity["entity_id"],
                entity["description"],
                output_path,
            )
            self._mark_provider(comic_id, "segment", self.mock_segment_provider.provider_name)
            return

        try:
            self.sam3_provider.segment_entity(
                image_path,
                entity["entity_id"],
                entity["description"],
                output_path,
            )
            self._mark_provider(comic_id, "segment", self.sam3_provider.provider_name)
        except Exception as error:
            if not settings.allow_mock_segment_fallback:
                raise ProviderError(f"SAM3 segmentation failed: {error}") from error
            self._append_warning(
                comic_id,
                f"SAM3 failed for {entity['entity_id']}; using mock segmentation fallback. {error}",
            )
            self.mock_segment_provider.segment_entity(
                image_path,
                entity["entity_id"],
                entity["description"],
                output_path,
            )
            self._mark_provider(
                comic_id,
                "segment",
                f"{self.sam3_provider.provider_name}+{self.mock_segment_provider.provider_name}",
            )

    def _apply_revision(
        self,
        comic_id: str,
        comic_dir: Path,
        storyboard: dict,
        entity_pool: dict,
        revision_plan: dict,
    ) -> dict:
        revisions_by_panel = {
            item["panel_id"]: item
            for item in revision_plan["panel_revisions"]
        }
        total_panels = len(storyboard["panels"])

        try:
            self._write_status(
                comic_id,
                "running",
                0,
                total_panels,
                f"Applying {revision_plan['revision_type']} revision",
            )

            for panel in storyboard["panels"]:
                panel_id = panel["panel_id"]
                if panel_id not in revisions_by_panel:
                    continue
                revision = revisions_by_panel[panel_id]
                panel["summary"] = revision["new_summary"]
                panel["text"] = revision.get("new_text", panel.get("text", []))
                self._write_status(
                    comic_id,
                    "running",
                    panel_id,
                    total_panels,
                    f"Regenerating panel {panel_id}",
                )
                self._generate_panel_assets(comic_id, comic_dir, storyboard, entity_pool, panel)

            self.store.save_json(comic_dir / "storyboard.json", storyboard)
            self.store.save_json(comic_dir / "entity_pool.json", entity_pool)
            self.store.save_json(comic_dir / "revision_plan.json", revision_plan)
            self._stitch_comic(comic_dir, storyboard)
            self._write_status(comic_id, "completed", total_panels, total_panels, "Completed")

            return {
                "comic_id": comic_id,
                "status": "completed",
                "revision_plan": revision_plan,
            }
        except Exception as error:
            self._write_status(comic_id, "failed", 0, total_panels, str(error))
            raise

    def _direct_panel_revision(
        self,
        storyboard: dict,
        panel_id: int,
        summary: str | None,
        text: list[dict] | None,
    ) -> dict:
        panel = next(
            (item for item in storyboard["panels"] if item["panel_id"] == panel_id),
            None,
        )
        if panel is None:
            raise ValueError(f"Panel not found: {panel_id}")

        valid_ids = {entity["entity_id"] for entity in storyboard.get("entities", [])}
        new_summary = " ".join((summary if summary is not None else panel["summary"]).split())
        if not new_summary:
            new_summary = panel["summary"]
        raw_text = text if text is not None else panel.get("text", [])

        return {
            "revision_type": "panel",
            "affected_panels": [panel_id],
            "regenerate_mode": "selected_only",
            "panel_revisions": [
                {
                    "panel_id": panel_id,
                    "new_summary": new_summary,
                    "new_text": validate_panel_text(raw_text, valid_ids),
                }
            ],
        }

    def _stitch_comic(self, comic_dir: Path, storyboard: dict) -> None:
        panel_paths = [
            comic_dir / "panels" / f"panel_{panel['panel_id']}.png"
            for panel in storyboard["panels"]
        ]
        stitch_panels(storyboard["layout"], panel_paths, comic_dir / "final_comic.png")

    def _entity_pool_summary(self, entity_pool: dict, entities_used: list[str]) -> dict:
        summary = {}
        for entity_id in entities_used:
            refs = entity_pool.get(entity_id, {}).get("refs", [])
            summary[entity_id] = [
                {"ref_id": ref["ref_id"], "note": ref.get("note", "")}
                for ref in refs
            ]
        return summary

    def _style_prompt(self, style: str) -> str:
        return settings.style_prompts.get(style, style)

    def _initial_provider_status(self) -> dict[str, str]:
        if settings.use_mock_providers:
            return {
                "mode": "mock",
                "storyboard_llm": "mock_llm",
                "reference_selector": "mock_llm",
                "revision_planner": "mock_llm",
                "ref_note_llm": "mock_llm",
                "image": "mock_image",
                "segment": "mock_segment",
            }
        return {
            "mode": "real_with_fallback",
            "storyboard_llm": "pending",
            "reference_selector": "pending",
            "revision_planner": "pending",
            "ref_note_llm": "pending",
            "image": "pending",
            "segment": "pending",
        }

    def _text_providers(self) -> tuple[OpenAIProvider, ...]:
        return (self.openai_provider,)

    def _status_path(self, comic_id: str) -> Path:
        return self.store.comic_dir(comic_id) / "status.json"

    def _read_status(self, comic_id: str) -> dict:
        path = self._status_path(comic_id)
        if not path.exists():
            return {
                "status": "running",
                "current_panel": 0,
                "total_panels": 0,
                "message": "",
                "warnings": [],
                "provider_status": self._initial_provider_status(),
            }
        return self.store.load_json(path)

    def _write_status(
        self,
        comic_id: str,
        status: str,
        current_panel: int,
        total_panels: int,
        message: str,
        warnings: list[str] | None = None,
        provider_status: dict | None = None,
    ) -> None:
        current = self._read_status(comic_id)
        self.store.save_json(
            self._status_path(comic_id),
            {
                "status": status,
                "current_panel": current_panel,
                "total_panels": total_panels,
                "message": message,
                "warnings": warnings if warnings is not None else current.get("warnings", []),
                "provider_status": provider_status
                if provider_status is not None
                else current.get("provider_status", self._initial_provider_status()),
            },
        )

    def _append_warning(self, comic_id: str, warning: str) -> None:
        status = self._read_status(comic_id)
        warnings = status.get("warnings", [])
        if warning not in warnings:
            warnings.append(warning)
        self._write_status(
            comic_id,
            status.get("status", "running"),
            status.get("current_panel", 0),
            status.get("total_panels", 0),
            status.get("message", ""),
            warnings=warnings,
            provider_status=status.get("provider_status", self._initial_provider_status()),
        )

    def _mark_provider(self, comic_id: str, key: str, value: str) -> None:
        status = self._read_status(comic_id)
        provider_status = status.get("provider_status", self._initial_provider_status())
        current_value = provider_status.get(key)
        if current_value and current_value not in {"pending", value}:
            parts = current_value.split("+")
            for part in value.split("+"):
                if part not in parts:
                    parts.append(part)
            provider_status[key] = "+".join(parts)
        else:
            provider_status[key] = value

        self._write_status(
            comic_id,
            status.get("status", "running"),
            status.get("current_panel", 0),
            status.get("total_panels", 0),
            status.get("message", ""),
            warnings=status.get("warnings", []),
            provider_status=provider_status,
        )
