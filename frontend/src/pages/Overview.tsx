import { useMetrics, useRiskScore } from "../api/hooks";

function bandClass(status: string): string {
  return status.toLowerCase();
}

export function Overview() {
  const metrics = useMetrics();
  const risk = useRiskScore();

  return (
    <section>
      <h2>Overview</h2>

      <div className="panel">
        <h3>Platform Risk Score</h3>
        {risk.isLoading && <p className="muted">Loading…</p>}
        {risk.isError && <p className="error">Failed to load risk score</p>}
        {risk.data && (
          <>
            <div className="gauge">
              {risk.data.score.toFixed(1)}
              <span className="unit"> / 100</span>{" "}
              <span className={`badge ${bandClass(risk.data.status)}`}>{risk.data.status}</span>
            </div>
            <p className="muted">
              Penalties — errors {risk.data.error_penalty}, alerts {risk.data.alert_penalty},
              incidents {risk.data.incident_penalty}
            </p>
          </>
        )}
      </div>

      <h3>Live Metrics</h3>
      {metrics.isLoading && <p className="muted">Loading…</p>}
      {metrics.isError && <p className="error">Failed to load metrics</p>}
      {metrics.data && (
        <div className="cards">
          <Metric label="Total Events" value={metrics.data.total_events} />
          <Metric label="Monitored Services" value={metrics.data.monitored_services} />
          <Metric label="Incidents" value={metrics.data.total_incidents} />
          <Metric label="Alerts Fired" value={metrics.data.total_alerts} />
        </div>
      )}
    </section>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="card">
      <div className="label">{label}</div>
      <div className="value">{value}</div>
    </div>
  );
}
