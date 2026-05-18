import type { ComicStatus } from "@/lib/types";

type Props = {
  status: ComicStatus;
};

export default function GenerationStatus({ status }: Props) {
  const progress =
    status.total_panels > 0
      ? Math.round((status.current_panel / status.total_panels) * 100)
      : 0;

  return (
    <div className="status-box">
      <div className="status-line">
        <strong>{status.status}</strong>
        <span>{progress}%</span>
      </div>
      <div className="progress-track">
        <div className="progress-fill" style={{ width: `${progress}%` }} />
      </div>
      <p>{status.message}</p>
      {status.provider_status ? (
        <div className="provider-grid">
          {Object.entries(status.provider_status).map(([key, value]) => (
            <span className="provider-chip" key={key}>
              {key}: {value}
            </span>
          ))}
        </div>
      ) : null}
    </div>
  );
}
