import { useNavigate } from "react-router-dom";

import { useIncidents } from "../api/hooks";
import { SeverityBadge } from "../components/SeverityBadge";

export function IncidentCenter() {
  const incidents = useIncidents();
  const navigate = useNavigate();

  return (
    <section>
      <h2>Incident Center</h2>
      {incidents.isLoading && <p className="muted">Loading…</p>}
      {incidents.isError && <p className="error">Failed to load incidents</p>}
      {incidents.data && incidents.data.length === 0 && (
        <p className="muted">No incidents yet. Ingest some events to see the pipeline work.</p>
      )}
      {incidents.data && incidents.data.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Title</th>
              <th>Service</th>
              <th>Category</th>
              <th>Severity</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {incidents.data.map((incident) => (
              <tr
                key={incident.id}
                className="clickable"
                onClick={() => navigate(`/incidents/${incident.id}`)}
              >
                <td>#{incident.id}</td>
                <td>{incident.title}</td>
                <td>{incident.service ?? "—"}</td>
                <td>{incident.category ?? "—"}</td>
                <td>
                  <SeverityBadge value={incident.severity} />
                </td>
                <td>{incident.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
