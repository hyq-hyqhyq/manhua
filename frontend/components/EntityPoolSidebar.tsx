import { assetUrl } from "@/lib/api";
import type { EntityPool } from "@/lib/types";

type Props = {
  entityPool: EntityPool;
};

export default function EntityPoolSidebar({ entityPool }: Props) {
  return (
    <aside className="entity-sidebar">
      <div className="section-heading compact">
        <p className="eyebrow">Entity Pool</p>
        <h2>Appearance history</h2>
      </div>
      <div className="entity-list">
        {Object.entries(entityPool).map(([entityId, entity]) => (
          <section className="entity-block" key={entityId}>
            <h3>{entityId}</h3>
            <p>{entity.description}</p>
            <div className="ref-list">
              {entity.refs.map((ref) => (
                <article className="ref-card" key={ref.ref_id}>
                  <img src={assetUrl(ref.rgba_path)} alt={`${entityId} ${ref.ref_id}`} />
                  <div>
                    <strong>{ref.ref_id}</strong>
                    <span>{ref.source}</span>
                    <p>{ref.note}</p>
                  </div>
                </article>
              ))}
            </div>
          </section>
        ))}
      </div>
    </aside>
  );
}
