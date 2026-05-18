"use client";

import { useState } from "react";

type Props = {
  disabled: boolean;
  loading: boolean;
  onApply: (feedback: string) => Promise<void>;
};

export default function GlobalRevisionBox({ disabled, loading, onApply }: Props) {
  const [feedback, setFeedback] = useState("");

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!feedback.trim()) {
      return;
    }
    await onApply(feedback.trim());
    setFeedback("");
  }

  return (
    <section className="editor-box">
      <div className="section-heading compact">
        <p className="eyebrow">Global revision</p>
        <h2>Revise the comic</h2>
      </div>
      <form onSubmit={handleSubmit}>
        <textarea
          value={feedback}
          onChange={(event) => setFeedback(event.target.value)}
          placeholder="Example: make the last panels more tense and the hero more frightened."
          rows={4}
          disabled={disabled}
        />
        <button className="secondary-button" type="submit" disabled={disabled || loading}>
          {loading ? "Applying..." : "Apply Global Revision"}
        </button>
      </form>
    </section>
  );
}
