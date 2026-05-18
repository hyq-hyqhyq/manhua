"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import ComicCanvas from "@/components/ComicCanvas";
import EntityPoolSidebar from "@/components/EntityPoolSidebar";
import GenerationStatus from "@/components/GenerationStatus";
import GlobalRevisionBox from "@/components/GlobalRevisionBox";
import PanelEditor from "@/components/PanelEditor";
import PanelGrid from "@/components/PanelGrid";
import {
  getComic,
  getComicStatus,
  reviseComicGlobal,
  reviseComicPanel
} from "@/lib/api";
import type { ComicResult, ComicStatus, Panel, RevisionPlan } from "@/lib/types";

export default function ComicResultPage() {
  const params = useParams();
  const comicId = useMemo(() => {
    const value = params.comic_id;
    return Array.isArray(value) ? value[0] : value;
  }, [params.comic_id]);

  const [comic, setComic] = useState<ComicResult | null>(null);
  const [status, setStatus] = useState<ComicStatus | null>(null);
  const [selectedPanelId, setSelectedPanelId] = useState<number | null>(null);
  const [revisionPlan, setRevisionPlan] = useState<RevisionPlan | null>(null);
  const [loading, setLoading] = useState(true);
  const [action, setAction] = useState<"global" | "panel" | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadComic = useCallback(async () => {
    if (!comicId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const [comicData, statusData] = await Promise.all([
        getComic(comicId),
        getComicStatus(comicId)
      ]);
      setComic(comicData);
      setStatus(statusData);
      setSelectedPanelId((current) => current ?? comicData.panels[0]?.panel_id ?? null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load comic");
    } finally {
      setLoading(false);
    }
  }, [comicId]);

  useEffect(() => {
    loadComic();
  }, [loadComic]);

  const selectedPanel: Panel | null = useMemo(() => {
    if (!comic || selectedPanelId === null) {
      return null;
    }
    return comic.panels.find((panel) => panel.panel_id === selectedPanelId) ?? null;
  }, [comic, selectedPanelId]);

  async function handleGlobalRevision(feedback: string) {
    if (!comicId) {
      return;
    }
    setAction("global");
    setError(null);
    try {
      const response = await reviseComicGlobal(comicId, feedback);
      setRevisionPlan(response.revision_plan);
      await loadComic();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Global revision failed");
      throw err;
    } finally {
      setAction(null);
    }
  }

  async function handlePanelRevision(panelId: number, feedback: string) {
    if (!comicId) {
      return;
    }
    setAction("panel");
    setError(null);
    try {
      const response = await reviseComicPanel(comicId, panelId, feedback);
      setRevisionPlan(response.revision_plan);
      await loadComic();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Panel revision failed");
      throw err;
    } finally {
      setAction(null);
    }
  }

  if (loading && !comic) {
    return (
      <main className="page-shell">
        <p className="muted">Loading comic...</p>
      </main>
    );
  }

  return (
    <main className="page-shell result-page">
      <section className="workspace">
        <div className="main-column">
          <div className="top-bar">
            <div>
              <p className="eyebrow">Comic ID</p>
              <h1>{comicId}</h1>
            </div>
            {status ? <GenerationStatus status={status} /> : null}
          </div>

          {error ? <div className="error-banner">{error}</div> : null}

          {comic ? (
            <>
              {comic.warnings.length > 0 ? (
                <section className="warning-box">
                  <strong>Warnings</strong>
                  {comic.warnings.map((warning) => (
                    <p key={warning}>{warning}</p>
                  ))}
                </section>
              ) : null}
              <ComicCanvas imagePath={comic.comic_page} />
              <GlobalRevisionBox
                disabled={action !== null}
                loading={action === "global"}
                onApply={handleGlobalRevision}
              />
              <PanelGrid
                panels={comic.panels}
                selectedPanelId={selectedPanelId}
                onSelect={setSelectedPanelId}
              />
              <PanelEditor
                panel={selectedPanel}
                disabled={action !== null}
                loading={action === "panel"}
                onRegenerate={handlePanelRevision}
              />
              {revisionPlan ? (
                <pre className="revision-plan">
                  {JSON.stringify(revisionPlan, null, 2)}
                </pre>
              ) : null}
            </>
          ) : null}
        </div>

        {comic ? <EntityPoolSidebar entityPool={comic.entity_pool} /> : null}
      </section>
    </main>
  );
}
