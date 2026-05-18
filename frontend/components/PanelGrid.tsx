import { assetUrl } from "@/lib/api";
import type { Panel } from "@/lib/types";
import ReferenceSheetViewer from "./ReferenceSheetViewer";

type Props = {
  panels: Panel[];
  selectedPanelId: number | null;
  onSelect: (panelId: number) => void;
};

export default function PanelGrid({ panels, selectedPanelId, onSelect }: Props) {
  return (
    <section className="panel-section">
      <div className="section-heading compact">
        <p className="eyebrow">Panels</p>
        <h2>Generated panel assets</h2>
      </div>
      <div className="panel-grid">
        {panels.map((panel) => (
          <button
            type="button"
            className={`panel-card ${selectedPanelId === panel.panel_id ? "selected" : ""}`}
            key={panel.panel_id}
            onClick={() => onSelect(panel.panel_id)}
          >
            <img src={assetUrl(panel.image_path)} alt={`Panel ${panel.panel_id}`} />
            <div className="panel-body">
              <strong>Panel {panel.panel_id}</strong>
              <p>{panel.summary}</p>
            </div>
            <ReferenceSheetViewer path={panel.reference_sheet_path} panelId={panel.panel_id} />
          </button>
        ))}
      </div>
    </section>
  );
}
