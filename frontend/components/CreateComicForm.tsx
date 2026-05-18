"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createComic } from "@/lib/api";
import type { LayoutName, StyleName } from "@/lib/types";

const layoutOptions: { value: LayoutName; label: string }[] = [
  { value: "1x4", label: "1x4 - 4 panels" },
  { value: "2x2", label: "2x2 - 4 panels" },
  { value: "2x3", label: "2x3 - 6 panels" },
  { value: "3x3", label: "3x3 - 9 panels" }
];

const styleOptions: { value: StyleName; label: string }[] = [
  { value: "black_white_manga", label: "Black and white manga" },
  { value: "color_webtoon", label: "Color webtoon" },
  { value: "american_comic", label: "American comic" },
  { value: "children_book", label: "Children book" },
  { value: "cinematic_comic", label: "Cinematic comic" }
];

export default function CreateComicForm() {
  const router = useRouter();
  const [prompt, setPrompt] = useState(
    "A teenage boy in a blue raincoat meets a talking gray cat on a rainy night."
  );
  const [layout, setLayout] = useState<LayoutName>("2x2");
  const [style, setStyle] = useState<StyleName>("black_white_manga");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const userPrompt = prompt.trim();
    if (!userPrompt) {
      setError("Story description is required.");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await createComic({
        user_prompt: userPrompt,
        layout,
        style
      });
      router.push(`/comics/${response.comic_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create comic.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className="create-form" onSubmit={handleSubmit}>
      <label className="field">
        <span>Story description</span>
        <textarea
          value={prompt}
          onChange={(event) => setPrompt(event.target.value)}
          rows={7}
        />
      </label>

      <div className="form-row">
        <label className="field">
          <span>Layout</span>
          <select
            value={layout}
            onChange={(event) => setLayout(event.target.value as LayoutName)}
          >
            {layoutOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        <label className="field">
          <span>Style</span>
          <select value={style} onChange={(event) => setStyle(event.target.value as StyleName)}>
            {styleOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      {error ? <div className="error-banner">{error}</div> : null}

      <button className="primary-button" type="submit" disabled={loading}>
        {loading ? "Generating..." : "Generate Comic"}
      </button>
    </form>
  );
}
