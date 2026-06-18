import { Link, useParams } from "react-router-dom";

import { useIncident } from "../api/hooks";
import { SeverityBadge } from "../components/SeverityBadge";

export function AIAnalysis() {
  const { id } = useParams();
  const incidentId = Number(id);
  const incident = useIncident(incidentId);

  if (incident.isLoading) return <p className="muted">Loading…</p>;
  if (incident.isError || !incident.data)
    return <p className="error">Failed to load incident</p>;

  const data = incident.data;
  const confidence =
    data.confidence_score != null ? `${Math.round(data.confidence_score * 100)}%` : "—";

  return (
    <section>
      <p>
        <Link to="/incidents" className="muted">
          ← Back to incidents
        </Link>
      </p>
      <h2>
        #{data.id} {data.title} <SeverityBadge value={data.severity} />
      </h2>

      <div className="panel">
        <h3>AI Analysis</h3>
        <p>
          <strong>Category:</strong> {data.category ?? "—"} &nbsp;|&nbsp;
          <strong> Confidence:</strong> {confidence}
        </p>
        <p>
          <strong>Root cause:</strong> {data.root_cause ?? "Pending triage…"}
        </p>
        <p>
          <strong>Summary:</strong> {data.summary ?? "Pending triage…"}
        </p>
      </div>

      <div className="panel">
        <h3>Recommended Actions</h3>
        {data.recommended_actions && data.recommended_actions.length > 0 ? (
          <ul className="actions">
            {data.recommended_actions.map((action, index) => (
              <li key={index}>{action}</li>
            ))}
          </ul>
        ) : (
          <p className="muted">No recommendations yet.</p>
        )}
        {data.runbook_references && data.runbook_references.length > 0 && (
          <p>
            <span className="muted">Runbooks: </span>
            {data.runbook_references.map((ref) => (
              <span key={ref.slug} className="pill">
                {ref.title}
              </span>
            ))}
          </p>
        )}
      </div>

      <div className="panel">
        <h3>Anomalies ({data.anomalies.length})</h3>
        <table>
          <thead>
            <tr>
              <th>Strategy</th>
              <th>Signature</th>
              <th>Score</th>
              <th>Baseline</th>
              <th>Current</th>
            </tr>
          </thead>
          <tbody>
            {data.anomalies.map((anomaly) => (
              <tr key={anomaly.id}>
                <td>{anomaly.strategy}</td>
                <td>{anomaly.signature ?? "—"}</td>
                <td>{anomaly.score.toFixed(2)}</td>
                <td>{anomaly.baseline_value.toFixed(2)}</td>
                <td>{anomaly.current_value.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
