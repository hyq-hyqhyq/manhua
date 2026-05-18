from __future__ import annotations

import re


def validate_storyboard(storyboard: dict, layout: str, style: str, panel_count: int) -> dict:
    if not isinstance(storyboard, dict):
        raise ValueError("Storyboard must be a JSON object")
    if storyboard.get("style") != style:
        raise ValueError(f"Storyboard style must be {style}")
    if storyboard.get("layout") != layout:
        raise ValueError(f"Storyboard layout must be {layout}")

    raw_entities = storyboard.get("entities")
    raw_panels = storyboard.get("panels")
    if not isinstance(raw_entities, list) or not raw_entities:
        raise ValueError("Storyboard must contain entities")
    if not isinstance(raw_panels, list):
        raise ValueError("Storyboard must contain panels")
    if len(raw_panels) != panel_count:
        raise ValueError(f"Storyboard panel count must be {panel_count}")

    entities = []
    id_map: dict[str, str] = {}
    used_ids: set[str] = set()
    for index, entity in enumerate(raw_entities):
        if not isinstance(entity, dict):
            raise ValueError("Each entity must be an object")
        raw_id = str(entity.get("entity_id") or f"entity_{index + 1}")
        entity_id = _stable_entity_id(raw_id, used_ids)
        description = str(entity.get("description") or entity_id)
        id_map[raw_id] = entity_id
        used_ids.add(entity_id)
        entities.append({"entity_id": entity_id, "description": description})

    valid_ids = {entity["entity_id"] for entity in entities}
    panels = []
    for expected_panel_id, panel in enumerate(raw_panels, start=1):
        if not isinstance(panel, dict):
            raise ValueError("Each panel must be an object")
        if int(panel.get("panel_id", 0)) != expected_panel_id:
            raise ValueError("Panel ids must start at 1 and increment by 1")
        raw_entities_used = panel.get("entities_used")
        if not isinstance(raw_entities_used, list):
            raise ValueError("Panel entities_used must be a list")
        entities_used = []
        for raw_id in raw_entities_used:
            normalized = id_map.get(str(raw_id), _normalize_entity_id(str(raw_id)))
            if normalized in valid_ids and normalized not in entities_used:
                entities_used.append(normalized)
        if not entities_used and entities:
            entities_used = [entities[0]["entity_id"]]

        panels.append(
            {
                "panel_id": expected_panel_id,
                "summary": str(panel.get("summary") or f"Panel {expected_panel_id}"),
                "entities_used": entities_used,
            }
        )

    return {
        "style": style,
        "layout": layout,
        "entities": entities,
        "panels": panels,
    }


def validate_reference_selection(selection: dict, panel: dict, entity_pool: dict) -> dict[str, list[str]]:
    if not isinstance(selection, dict) or not isinstance(selection.get("selected_refs"), dict):
        raise ValueError("Reference selection must contain selected_refs")

    allowed_entities = set(panel["entities_used"])
    selected_entities = set(selection["selected_refs"].keys())
    if selected_entities - allowed_entities:
        raise ValueError("Reference selection included entities not used in the panel")

    result: dict[str, list[str]] = {}
    for entity_id in panel["entities_used"]:
        refs = entity_pool.get(entity_id, {}).get("refs", [])
        valid_ref_ids = {ref["ref_id"] for ref in refs}
        raw_selected = selection["selected_refs"].get(entity_id, [])
        if not isinstance(raw_selected, list):
            raw_selected = []

        selected = []
        for ref_id in raw_selected:
            ref_id = str(ref_id)
            if ref_id in valid_ref_ids and ref_id not in selected:
                selected.append(ref_id)

        anchor_id = next(
            (ref["ref_id"] for ref in refs if ref.get("source") == "anchor"),
            None,
        )
        if anchor_id and anchor_id not in selected:
            selected.insert(0, anchor_id)

        if not selected and refs:
            selected = [ref["ref_id"] for ref in refs[:3]]

        result[entity_id] = selected[:3]

    return result


def refs_from_selected_ids(entity_pool: dict, selected_ids: dict[str, list[str]]) -> dict[str, list[dict]]:
    selected_refs: dict[str, list[dict]] = {}
    for entity_id, ref_ids in selected_ids.items():
        refs = entity_pool.get(entity_id, {}).get("refs", [])
        refs_by_id = {ref["ref_id"]: ref for ref in refs}
        selected_refs[entity_id] = [
            refs_by_id[ref_id]
            for ref_id in ref_ids
            if ref_id in refs_by_id
        ]
    return selected_refs


def validate_revision_plan(
    revision_plan: dict,
    storyboard: dict,
    revision_type: str,
    panel_id: int | None = None,
) -> dict:
    if not isinstance(revision_plan, dict):
        raise ValueError("Revision plan must be an object")
    if revision_plan.get("revision_type") not in {"global", "panel"}:
        raise ValueError("Revision type must be global or panel")
    if revision_plan.get("revision_type") != revision_type:
        raise ValueError(f"Revision type must be {revision_type}")

    valid_panel_ids = {panel["panel_id"] for panel in storyboard["panels"]}
    raw_affected = revision_plan.get("affected_panels")
    raw_revisions = revision_plan.get("panel_revisions")
    if not isinstance(raw_affected, list) or not isinstance(raw_revisions, list):
        raise ValueError("Revision plan missing affected_panels or panel_revisions")

    affected = []
    for raw_id in raw_affected:
        current_id = int(raw_id)
        if current_id in valid_panel_ids and current_id not in affected:
            affected.append(current_id)

    if revision_type == "panel":
        if panel_id is None:
            raise ValueError("panel_id is required")
        affected = [panel_id]
        regenerate_mode = "selected_only"
    else:
        if not affected:
            raise ValueError("Global revision must affect at least one panel")
        regenerate_mode = revision_plan.get("regenerate_mode") or "affected_panels"
        if regenerate_mode not in {"affected_panels", "from_panel_k"}:
            regenerate_mode = "affected_panels"

    panel_revisions = []
    revisions_by_id = {
        int(item.get("panel_id")): item
        for item in raw_revisions
        if isinstance(item, dict) and item.get("panel_id") is not None
    }
    for current_id in affected:
        item = revisions_by_id.get(current_id)
        if not item:
            original = next(panel for panel in storyboard["panels"] if panel["panel_id"] == current_id)
            new_summary = original["summary"]
        else:
            new_summary = str(item.get("new_summary") or "")
        if not new_summary:
            raise ValueError(f"Missing new_summary for panel {current_id}")
        panel_revisions.append({"panel_id": current_id, "new_summary": new_summary})

    return {
        "revision_type": revision_type,
        "affected_panels": affected,
        "regenerate_mode": regenerate_mode,
        "panel_revisions": panel_revisions,
    }


def _stable_entity_id(raw_id: str, used_ids: set[str]) -> str:
    base = _normalize_entity_id(raw_id) or "entity"
    entity_id = base
    suffix = 2
    while entity_id in used_ids:
        entity_id = f"{base}_{suffix}"
        suffix += 1
    return entity_id


def _normalize_entity_id(raw_id: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9_]+", "_", raw_id.strip().lower())
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized[:32]
