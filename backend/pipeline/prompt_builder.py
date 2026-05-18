from __future__ import annotations

import json


JSON_SYSTEM_PROMPT = (
    "You are a strict JSON generator for an interactive comic generation pipeline. "
    "Return valid JSON only. Do not include Markdown fences, comments, or explanations. "
    "Do not add fields that are not requested."
)


def storyboard_prompt(
    user_prompt: str,
    layout: str,
    style: str,
    panel_count: int,
    style_prompt: str,
) -> str:
    payload = {
        "user_prompt": user_prompt,
        "layout": layout,
        "style": style,
        "panel_count": panel_count,
        "style_prompt": style_prompt,
    }

    return f'''
You are the Storyboard Planner for a multi-panel comic generation system.

Your job:
Convert the user's story into a minimal storyboard JSON. The storyboard will be used by a later image generation pipeline, so it must be clear, consistent, and easy to execute.

Input:
{json.dumps(payload, ensure_ascii=False, indent=2)}

Output JSON shape:
{{
  "style": "{style}",
  "layout": "{layout}",
  "entities": [
    {{
      "entity_id": "short_stable_id",
      "description": "stable visual description"
    }}
  ],
  "panels": [
    {{
      "panel_id": 1,
      "summary": "visual description of this panel",
      "entities_used": ["entity_id"],
      "text": [
        {{
          "type": "speech|thought|caption|sfx",
          "speaker": "entity_id or null",
          "content": "short comic text",
          "position": "top_left|top_center|top_right|middle_left|middle_right|bottom_left|bottom_center|bottom_right"
        }}
      ]
    }}
  ]
}}

Hard rules:
- Return JSON only.
- Do not use Markdown.
- Do not add extra fields.
- "style" must be exactly "{style}".
- "layout" must be exactly "{layout}".
- "panels" length must be exactly {panel_count}.
- panel_id must start at 1 and increase by 1.
- entities_used must only contain entity_id values defined in entities.
- Every important recurring character, animal, object, or special scene element should be listed in entities.
- entity_id must be short, lowercase, stable, and easy to reuse, such as "boy", "cat", "girl", "robot", "sword", "station".
- Do not create multiple ids for the same entity.
- Each entity description must focus on stable visual identity: age/type, body shape, color, clothing, distinctive features.
- Panel summaries must be visual, concrete, and suitable for image generation.
- Panel summaries should describe action, composition, mood, and scene context, but remain concise.
- Keep continuity across panels.
- Distribute the story naturally across exactly {panel_count} panels.
- If the user prompt is vague, invent a simple coherent comic story, but keep it consistent.
- Each panel may contain 0 to 2 text items.
- Keep text short and visually manageable.
- speech and thought should be short dialogue-like text.
- caption should be short narration or scene-setting text.
- sfx should be very short sound-effect text.
- Do not generate long paragraphs.
'''.strip()


def reference_selection_prompt(
    panel: dict,
    entities: list[dict],
    entity_pool_summary: dict,
) -> str:
    payload = {
        "panel": {
            "panel_id": panel["panel_id"],
            "summary": panel["summary"],
            "entities_used": panel["entities_used"],
        },
        "entities": entities,
        "entity_pool_summary": entity_pool_summary,
    }

    return f'''
You are the Reference Selector for an Entity-Pool-based comic generation system.

Context:
Each entity in the Entity Pool has an appearance history. Multiple refs under the same entity show the same entity in different views, poses, expressions, or contexts. They are not different characters.

Your job:
For the current panel, select the most useful refs for each entity that appears in this panel. These refs will be combined into one reference sheet and sent to an image generation model.

Input:
{json.dumps(payload, ensure_ascii=False, indent=2)}

Output JSON shape:
{{
  "selected_refs": {{
    "entity_id": ["ref_id"]
  }}
}}

Hard rules:
- Return JSON only.
- Do not use Markdown.
- Do not add extra fields.
- Include every entity in panel.entities_used as a key in selected_refs.
- Do not include entities that are not in panel.entities_used.
- For each entity, select 1 to 3 refs if refs exist.
- If an entity has no refs, return an empty list for that entity.
- Only select ref_id values that actually exist in entity_pool_summary.
- Prefer anchor refs when available because they preserve identity.
- Also select refs whose note is relevant to the current panel action, pose, expression, or camera view.
- If many refs are relevant, choose at most 3: one identity anchor and up to two context-relevant refs.
- Do not select too many similar refs.
- Do not hallucinate ref_id values.
'''.strip()


def revision_prompt(
    storyboard: dict,
    feedback: str,
    revision_type: str,
    panel_id: int | None = None,
) -> str:
    payload = {
        "storyboard": storyboard,
        "feedback": feedback,
        "revision_type": revision_type,
        "selected_panel_id": panel_id,
    }

    return f'''
You are the Revision Planner for an interactive multi-panel comic system.

Your job:
Convert the user's feedback into a minimal revision plan. The system will regenerate only the affected panels, so choose affected_panels carefully.

Input:
{json.dumps(payload, ensure_ascii=False, indent=2)}

Output JSON shape:
{{
  "revision_type": "global",
  "affected_panels": [1],
  "regenerate_mode": "affected_panels",
  "panel_revisions": [
    {{
      "panel_id": 1,
      "new_summary": "updated visual panel summary",
      "new_text": [
        {{
          "type": "speech|thought|caption|sfx",
          "speaker": "entity_id or null",
          "content": "short comic text",
          "position": "top_left|top_center|top_right|middle_left|middle_right|bottom_left|bottom_center|bottom_right"
        }}
      ]
    }}
  ]
}}

Allowed values:
- revision_type: "global" or "panel"
- regenerate_mode: "affected_panels", "selected_only", or "from_panel_k"

Hard rules:
- Return JSON only.
- Do not use Markdown.
- Do not add extra fields.
- affected_panels must contain valid panel_id values from the storyboard.
- panel_revisions must contain exactly one item for each affected panel.
- Each new_summary must be a complete visual description for image generation.
- Each new_text must be a complete replacement text array for that panel.
- Preserve story continuity unless the feedback explicitly asks to change the story.
- Preserve existing entities unless the feedback explicitly adds or removes an entity.
- Do not rewrite unaffected panels.
- Do not change style or layout.
- Each revised panel may contain 0 to 2 text items.
- Keep text short and visually manageable.

Global revision rules:
- If revision_type is "global", choose only the panels that actually need regeneration.
- Use regenerate_mode "affected_panels" unless the feedback changes the story from a specific point onward.
- If the feedback changes the story from a specific panel onward, use regenerate_mode "from_panel_k" and include all panels from that point to the end.

Panel revision rules:
- If revision_type is "panel", affected_panels must contain only selected_panel_id.
- If revision_type is "panel", regenerate_mode must be "selected_only".
- Only rewrite the selected panel summary and selected panel text.
- Keep the revised panel consistent with neighboring panels.

User feedback should be followed directly, but do not add unnecessary changes.
'''.strip()


def ref_note_prompt(panel_summary: str, entity: dict) -> str:
    payload = {
        "entity": entity,
        "panel_summary": panel_summary,
    }

    return f'''
You are writing a short searchable appearance note for one entity cut out from a generated comic panel.

Purpose:
The note will be used later to choose useful references from the Entity Pool.

Input:
{json.dumps(payload, ensure_ascii=False, indent=2)}

Write one concise phrase under 14 words.

The phrase should mention useful visual retrieval cues, such as:
- view angle
- pose
- action
- expression
- held object
- camera distance
- special clothing or state

Good examples:
front half-body, neutral expression
side view, holding flashlight
full body, running
close-up, nervous expression
sitting on boy shoulder
wet raincoat, standing in rain

Bad examples:
nice image
good reference
same character
panel appearance
beautiful style

Rules:
- Return plain text only.
- No JSON.
- No quotation marks.
- No full sentence.
- No period.
- Do not mention entity_id unless necessary.
'''.strip()


def panel_image_prompt(
    panel: dict,
    style_prompt: str,
    entities_used: list[dict],
) -> str:
    payload = {
        "panel_id": panel["panel_id"],
        "panel_summary": panel["summary"],
        "entities_used": entities_used,
        "text": panel.get("text", []),
    }

    return f'''
Create one comic panel with readable comic text.

Style:
{style_prompt}

Image A is the entity reference sheet.
Each row corresponds to one entity.
All references in the same row show the same entity in different appearances, not different characters.

Panel input:
{json.dumps(payload, ensure_ascii=False, indent=2)}

Text rendering requirements:
- Render all provided text exactly as written.
- Put speech text inside speech balloons.
- Put thought text inside thought balloons.
- Put caption text inside caption boxes.
- Put sfx text as stylized comic sound effects.
- Follow the requested approximate position.
- Make all text clear, readable, and correctly spelled.
- Do not invent extra text.
- Do not omit provided text.
- Keep text balloons or caption boxes from covering important faces or key objects.

Visual requirements:
- Preserve the identity and appearance of entities from the reference sheet.
- Use only the entities listed for this panel as main subjects.
- Do not create extra main characters.
- Do not merge different entities.
- Keep the visual style consistent with the whole comic.
- Make the panel composition clear and readable.
- Follow the panel summary closely.
- The output should be one clean comic panel.
'''.strip()
