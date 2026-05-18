from config import settings


class MockStoryboardPlanner:
    def plan(self, user_prompt: str, layout: str, style: str) -> dict:
        if layout not in settings.layouts:
            raise ValueError(f"Unsupported layout: {layout}")
        if style not in settings.styles:
            raise ValueError(f"Unsupported style: {style}")

        panel_count = settings.layouts[layout]["panel_count"]
        entities = self._mock_entities(user_prompt)
        panels = self._mock_panels(user_prompt, entities, panel_count)

        return {
            "style": style,
            "layout": layout,
            "entities": entities,
            "panels": panels,
        }

    def _mock_entities(self, user_prompt: str) -> list[dict[str, str]]:
        lowered = user_prompt.lower()
        entities: list[dict[str, str]] = []

        if any(token in user_prompt for token in ("少年", "男孩")) or "boy" in lowered:
            entities.append(
                {
                    "entity_id": "boy",
                    "description": "teenage boy, slim, short messy black hair, blue raincoat",
                }
            )
        else:
            entities.append(
                {
                    "entity_id": "hero",
                    "description": "main character from the story prompt, expressive face, clear silhouette",
                }
            )

        if "猫" in user_prompt or "cat" in lowered:
            entities.append(
                {
                    "entity_id": "cat",
                    "description": "small gray cat, green eyes, wet fur, alert posture",
                }
            )
        elif "dog" in lowered or "狗" in user_prompt:
            entities.append(
                {
                    "entity_id": "dog",
                    "description": "loyal small dog, bright eyes, energetic posture",
                }
            )
        else:
            entities.append(
                {
                    "entity_id": "companion",
                    "description": "important companion object or character from the prompt",
                }
            )

        return entities

    def _mock_panels(
        self, user_prompt: str, entities: list[dict[str, str]], panel_count: int
    ) -> list[dict]:
        entity_ids = [entity["entity_id"] for entity in entities]
        first = entity_ids[:1]
        all_entities = entity_ids[:]
        prompt_hint = self._shorten(user_prompt, 92)
        beats = [
            f"Opening beat: the story begins with {prompt_hint}.",
            "The main character notices a strange detail that changes the mood.",
            "The companion or mystery enters the scene and draws attention.",
            "The characters move closer as the atmosphere becomes more intense.",
            "A surprising reaction reveals the emotional stakes.",
            "The setting pushes the characters into a clear decision.",
            "The tension peaks with a bold visual moment.",
            "The characters react and the scene pivots toward resolution.",
            "Final beat: the moment lands with a clear comic ending.",
        ]
        panels: list[dict] = []

        for index in range(panel_count):
            if index == 0:
                used = first
            elif index == panel_count - 1:
                used = all_entities
            elif index % 2 == 0:
                used = all_entities
            else:
                used = entity_ids[: min(len(entity_ids), 2)]

            panels.append(
                {
                    "panel_id": index + 1,
                    "summary": beats[index] if index < len(beats) else beats[-1],
                    "entities_used": used,
                    "text": self._mock_text(index, panel_count, used),
                }
            )

        return panels

    def _mock_text(self, index: int, panel_count: int, entities_used: list[str]) -> list[dict]:
        if index == 0:
            return [
                {
                    "type": "caption",
                    "speaker": None,
                    "content": "雨夜开始。",
                    "position": "top_left",
                }
            ]
        if index == panel_count - 1:
            speaker = entities_used[-1] if entities_used else None
            return [
                {
                    "type": "speech",
                    "speaker": speaker,
                    "content": "就是现在。",
                    "position": "top_right",
                }
            ]
        if index % 2 == 0:
            return [
                {
                    "type": "sfx",
                    "speaker": None,
                    "content": "沙沙",
                    "position": "middle_right",
                }
            ]
        return []

    def _shorten(self, text: str, limit: int) -> str:
        collapsed = " ".join(text.split())
        if len(collapsed) <= limit:
            return collapsed
        return collapsed[: limit - 3].rstrip() + "..."
