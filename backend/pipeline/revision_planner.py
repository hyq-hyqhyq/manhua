class MockRevisionPlanner:
    def plan_global(self, storyboard: dict, feedback: str) -> dict:
        panels = storyboard["panels"]
        total = len(panels)
        start_panel = max(1, total // 2)
        affected_panels = list(range(start_panel, total + 1))
        panel_revisions = []

        for panel in panels:
            if panel["panel_id"] in affected_panels:
                panel_revisions.append(
                    {
                        "panel_id": panel["panel_id"],
                        "new_summary": self._with_feedback(panel["summary"], feedback),
                        "new_text": self._with_text_feedback(panel.get("text", []), feedback),
                    }
                )

        return {
            "revision_type": "global",
            "affected_panels": affected_panels,
            "regenerate_mode": "affected_panels",
            "panel_revisions": panel_revisions,
        }

    def plan_panel(self, storyboard: dict, panel_id: int, feedback: str) -> dict:
        panel = next(
            (item for item in storyboard["panels"] if item["panel_id"] == panel_id),
            None,
        )
        if panel is None:
            raise ValueError(f"Panel not found: {panel_id}")

        return {
            "revision_type": "panel",
            "affected_panels": [panel_id],
            "regenerate_mode": "selected_only",
            "panel_revisions": [
                {
                    "panel_id": panel_id,
                    "new_summary": self._with_feedback(panel["summary"], feedback),
                    "new_text": self._with_text_feedback(panel.get("text", []), feedback),
                }
            ],
        }

    def _with_feedback(self, summary: str, feedback: str) -> str:
        cleaned = " ".join(feedback.split())
        if len(cleaned) > 110:
            cleaned = cleaned[:107].rstrip() + "..."
        return f"{summary} Revision note: {cleaned}"

    def _with_text_feedback(self, text_items: list, feedback: str) -> list:
        if isinstance(text_items, list) and text_items:
            return text_items[:2]

        cleaned = " ".join(feedback.split())
        if len(cleaned) > 16:
            cleaned = cleaned[:16].rstrip()
        return [
            {
                "type": "caption",
                "speaker": None,
                "content": cleaned or "气氛改变。",
                "position": "top_left",
            }
        ]
