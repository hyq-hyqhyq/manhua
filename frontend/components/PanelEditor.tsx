"use client";

import { useEffect, useState } from "react";
import type { Panel } from "@/lib/types";

type Props = {
  panel: Panel | null;
  disabled: boolean;
  loading: boolean;
  onRegenerate: (panelId: number, feedback: string) => Promise<void>;
};

export default function PanelEditor({ panel, disabled, loading, onRegenerate }: Props) {
  const [feedback, setFeedback] = useState("");

  useEffect(() => {
    setFeedback("");
  }, [panel?.panel_id]);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!panel || !feedback.trim()) {
      return;
    }
    await onRegenerate(panel.panel_id, feedback.trim());
    setFeedback("");
  }

  return (
    <section className="editor-box">
      <div className="section-heading compact">
        <p className="eyebrow">Panel revision</p>
        <h2>{panel ? `Panel ${panel.panel_id}` : "No panel selected"}</h2>
      </div>
      <p className="muted">{panel?.summary ?? "Select a panel to edit it."}</p>
      <form onSubmit={handleSubmit}>
        <textarea
          value={feedback}
          onChange={(event) => setFeedback(event.target.value)}
          placeholder="Describe how this panel should change."
          rows={4}
          disabled={!panel || disabled}
        />
        <button className="secondary-button" type="submit" disabled={!panel || disabled || loading}>
          {loading ? "Regenerating..." : "Regenerate This Panel"}
        </button>
      </form>
    </section>
  );
}
