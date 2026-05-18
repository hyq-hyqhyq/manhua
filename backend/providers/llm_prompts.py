from __future__ import annotations

import json


JSON_SYSTEM_PROMPT = (
    "You are a careful comic planning assistant. Return valid JSON only. "
    "Do not include Markdown fences or explanatory text."
)


def storyboard_prompt(
    user_prompt: str,
    layout: str,
    style: str,
    panel_count: int,
    style_prompt: str,
) -> str:
    return f"""
Generate a minimal storyboard JSON for a multi-panel comic.

Input:
{json.dumps({
    "user_prompt": user_prompt,
    "layout": layout,
    "style": style,
    "panel_count": panel_count,
    "style_prompt": style_prompt,
}, ensure_ascii=False)}

Rules:
- Return only this JSON shape: {{"style": str, "layout": str, "entities": [{{"entity_id": str, "description": str}}], "panels": [{{"panel_id": int, "summary": str, "entities_used": [str]}}]}}
- panels length must be exactly {panel_count}.
- panel_id starts at 1 and increments by 1.
- entities_used must only reference existing entity_id values.
- entity_id values should be short and stable, such as boy, cat, girl, robot, sword.
- Do not add any extra fields.
""".strip()


def reference_selection_prompt(panel: dict, entities: list[dict], entity_pool_summary: dict) -> str:
    return f"""
Choose the most useful Entity Pool refs for this comic panel.

Input:
{json.dumps({
    "panel_id": panel["panel_id"],
    "panel_summary": panel["summary"],
    "entities_used": panel["entities_used"],
    "entities": entities,
    "entity_pool_summary": entity_pool_summary,
}, ensure_ascii=False)}

Rules:
- Return only this JSON shape: {{"selected_refs": {{"entity_id": ["ref_id"]}}}}.
- For each entity, choose 1 to 3 refs when refs exist.
- Prefer anchor refs when present.
- Choose refs relevant to the current panel summary.
- If an entity has no refs, return an empty list for that entity.
- Do not include image data or extra fields.
""".strip()


def revision_prompt(
    storyboard: dict,
    feedback: str,
    revision_type: str,
    panel_id: int | None = None,
) -> str:
    return f"""
Plan a comic revision.

Input:
{json.dumps({
    "storyboard": storyboard,
    "feedback": feedback,
    "revision_type": revision_type,
    "panel_id": panel_id,
}, ensure_ascii=False)}

Rules:
- For global revision, choose affected_panels that need regeneration.
- For panel revision, affected_panels must contain only panel_id.
- affected_panels must be valid panel ids.
- Keep story continuity.
- Return only this JSON shape: {{"revision_type": "global|panel", "affected_panels": [int], "regenerate_mode": "affected_panels|selected_only|from_panel_k", "panel_revisions": [{{"panel_id": int, "new_summary": str}}]}}.
- Do not add extra fields.
""".strip()


def ref_note_prompt(panel_summary: str, entity: dict) -> str:
    return f"""
Write a short appearance note for one entity cut out from a comic panel.

Entity:
{json.dumps(entity, ensure_ascii=False)}

Panel summary:
{panel_summary}

Return one concise phrase under 14 words. No JSON. No quotation marks.
""".strip()
