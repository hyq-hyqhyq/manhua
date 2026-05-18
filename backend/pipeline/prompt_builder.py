def build_panel_prompt(panel: dict, style_prompt: str, entities_by_id: dict[str, dict]) -> str:
    entity_lines = []
    for entity_id in panel["entities_used"]:
        description = entities_by_id.get(entity_id, {}).get("description", "")
        entity_lines.append(f"- {entity_id}: {description}")

    entities_text = "\n".join(entity_lines) if entity_lines else "- none"
    return f"""
Create one comic panel.

Style:
{style_prompt}

Image A is the entity reference sheet.
Each row corresponds to one entity.
All references in the same row show the same entity, not different characters.

Entities in this panel:
{entities_text}

Current panel:
{panel["summary"]}

Requirements:
- Preserve the identity and appearance of the entities from the reference sheet.
- Do not create extra main characters.
- Do not merge different entities.
- Keep the visual style consistent with the whole comic.
- Do not include readable text unless explicitly requested.
- The output should be one clean comic panel.
""".strip()
