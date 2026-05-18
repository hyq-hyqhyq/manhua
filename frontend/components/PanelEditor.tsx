"use client";

import { useEffect, useState } from "react";
import type {
  Panel,
  PanelTextItem,
  PanelTextPosition,
  PanelTextType,
  StoryboardEntity
} from "@/lib/types";

type Props = {
  panel: Panel | null;
  entities: StoryboardEntity[];
  disabled: boolean;
  loading: boolean;
  onRegenerate: (
    panelId: number,
    feedback: string,
    summary: string,
    text: PanelTextItem[]
  ) => Promise<void>;
};

const textTypes: PanelTextType[] = ["speech", "thought", "caption", "sfx"];
const textPositions: PanelTextPosition[] = [
  "top_left",
  "top_center",
  "top_right",
  "middle_left",
  "middle_right",
  "bottom_left",
  "bottom_center",
  "bottom_right"
];

const emptyTextItem = (): PanelTextItem => ({
  type: "speech",
  speaker: null,
  content: "",
  position: "top_right"
});

export default function PanelEditor({
  panel,
  entities,
  disabled,
  loading,
  onRegenerate
}: Props) {
  const [feedback, setFeedback] = useState("");
  const [summary, setSummary] = useState("");
  const [textItems, setTextItems] = useState<PanelTextItem[]>([]);

  useEffect(() => {
    setFeedback("");
    setSummary(panel?.summary ?? "");
    setTextItems(panel?.text ?? []);
  }, [panel?.panel_id, panel?.summary, panel?.text]);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!panel) {
      return;
    }

    const cleanedText = textItems
      .map((item) => ({
        ...item,
        content: item.content.trim(),
        speaker: item.speaker || null
      }))
      .filter((item) => item.content)
      .slice(0, 2);

    await onRegenerate(
      panel.panel_id,
      feedback.trim() || "Manual panel text edit",
      summary.trim() || panel.summary,
      cleanedText
    );
    setFeedback("");
  }

  function updateTextItem(index: number, patch: Partial<PanelTextItem>) {
    setTextItems((current) =>
      current.map((item, itemIndex) =>
        itemIndex === index ? { ...item, ...patch } : item
      )
    );
  }

  function addTextItem() {
    setTextItems((current) =>
      current.length >= 2 ? current : [...current, emptyTextItem()]
    );
  }

  function removeTextItem(index: number) {
    setTextItems((current) => current.filter((_, itemIndex) => itemIndex !== index));
  }

  return (
    <section className="editor-box">
      <div className="section-heading compact">
        <p className="eyebrow">Panel revision</p>
        <h2>{panel ? `Panel ${panel.panel_id}` : "No panel selected"}</h2>
      </div>
      <form onSubmit={handleSubmit}>
        <label className="field">
          Summary
          <textarea
            value={summary}
            onChange={(event) => setSummary(event.target.value)}
            placeholder="Visual summary for this panel."
            rows={4}
            disabled={!panel || disabled}
          />
        </label>

        <div className="panel-text-editor">
          <div className="inline-heading">
            <strong>Text</strong>
            <button
              type="button"
              className="small-button"
              onClick={addTextItem}
              disabled={!panel || disabled || textItems.length >= 2}
            >
              Add Text
            </button>
          </div>
          {textItems.length === 0 ? (
            <p className="muted">No comic text in this panel.</p>
          ) : null}
          {textItems.map((item, index) => (
            <div className="text-item-editor" key={index}>
              <select
                value={item.type}
                onChange={(event) =>
                  updateTextItem(index, { type: event.target.value as PanelTextType })
                }
                disabled={!panel || disabled}
              >
                {textTypes.map((type) => (
                  <option key={type} value={type}>
                    {type}
                  </option>
                ))}
              </select>
              <select
                value={item.speaker ?? ""}
                onChange={(event) =>
                  updateTextItem(index, { speaker: event.target.value || null })
                }
                disabled={!panel || disabled}
              >
                <option value="">no speaker</option>
                {entities.map((entity) => (
                  <option key={entity.entity_id} value={entity.entity_id}>
                    {entity.entity_id}
                  </option>
                ))}
              </select>
              <select
                value={item.position}
                onChange={(event) =>
                  updateTextItem(index, {
                    position: event.target.value as PanelTextPosition
                  })
                }
                disabled={!panel || disabled}
              >
                {textPositions.map((position) => (
                  <option key={position} value={position}>
                    {position}
                  </option>
                ))}
              </select>
              <input
                value={item.content}
                onChange={(event) => updateTextItem(index, { content: event.target.value })}
                placeholder="short comic text"
                disabled={!panel || disabled}
              />
              <button
                type="button"
                className="small-button danger"
                onClick={() => removeTextItem(index)}
                disabled={!panel || disabled}
              >
                Remove
              </button>
            </div>
          ))}
        </div>

        <label className="field">
          Feedback
          <textarea
            value={feedback}
            onChange={(event) => setFeedback(event.target.value)}
            placeholder="Optional: describe how this panel should change."
            rows={3}
            disabled={!panel || disabled}
          />
        </label>
        <button className="secondary-button" type="submit" disabled={!panel || disabled || loading}>
          {loading ? "Regenerating..." : "Save and Regenerate This Panel"}
        </button>
      </form>
    </section>
  );
}
