import { useTopology } from "../api/hooks";

export function Topology() {
  const topology = useTopology();

  return (
    <section>
      <h2>Service Topology</h2>
      <p className="muted">
        Services bordered in red are impacted by an open incident (blast radius).
      </p>
      {topology.isLoading && <p className="muted">Loading…</p>}
      {topology.isError && <p className="error">Failed to load topology</p>}
      {topology.data && topology.data.nodes.length === 0 && (
        <p className="muted">No topology configured.</p>
      )}
      {topology.data && (
        <div className="cards">
          {topology.data.nodes.map((node) => (
            <div
              key={node.service}
              className={`topology-node${node.impacted ? " impacted" : ""}`}
            >
              <strong>{node.service}</strong>
              {node.impacted && <span className="badge critical"> impacted</span>}
              <div style={{ marginTop: 8 }}>
                {node.depends_on.length > 0 ? (
                  node.depends_on.map((dep) => (
                    <span key={dep} className="pill">
                      → {dep}
                    </span>
                  ))
                ) : (
                  <span className="muted">no dependencies</span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
