"""Integration tests for the incidents API."""

from datetime import UTC, datetime

from backend.app.incidents.incident_service import IncidentService
from backend.app.models.anomaly import Anomaly
from backend.app.models.enums import IncidentStatus

_NOW = datetime(2026, 6, 18, 10, 0, 0, tzinfo=UTC)


def _seed_incident(db, n_anomalies=2, service="payment-api"):
    anomalies = [
        Anomaly(
            strategy="z_score",
            service=service,
            signature=None,
            score=9.0,
            baseline_value=10.0,
            current_value=70.0,
            window_start=_NOW,
            window_end=_NOW,
        )
        for _ in range(n_anomalies)
    ]
    db.add_all(anomalies)
    db.commit()
    return IncidentService(db).open_incident(service, anomalies, _NOW)


class TestIncidentsApi:
    def test_list_empty(self, client):
        response = client.get("/api/v1/incidents")

        assert response.status_code == 200
        assert response.json() == []

    def test_list_returns_created_incident(self, client, db):
        _seed_incident(db)

        response = client.get("/api/v1/incidents")

        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert body[0]["service"] == "payment-api"
        assert body[0]["severity"] == "MEDIUM"
        assert len(body[0]["anomalies"]) == 2

    def test_get_by_id(self, client, db):
        incident = _seed_incident(db)

        response = client.get(f"/api/v1/incidents/{incident.id}")

        assert response.status_code == 200
        assert response.json()["id"] == incident.id

    def test_get_unknown_returns_404(self, client):
        response = client.get("/api/v1/incidents/999")

        assert response.status_code == 404
        assert response.json()["code"] == "incident_not_found"

    def test_filter_by_status(self, client, db):
        _seed_incident(db)

        open_response = client.get(f"/api/v1/incidents?status={IncidentStatus.OPEN.value}")
        resolved_response = client.get(f"/api/v1/incidents?status={IncidentStatus.RESOLVED.value}")

        assert len(open_response.json()) == 1
        assert resolved_response.json() == []


class TestPatchIncidentStatus:
    def test_resolve_sets_status_and_resolved_at(self, client, db):
        incident = _seed_incident(db)

        response = client.patch(
            f"/api/v1/incidents/{incident.id}",
            json={"status": IncidentStatus.RESOLVED.value},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == IncidentStatus.RESOLVED.value
        assert body["resolved_at"] is not None

    def test_acknowledge_does_not_set_resolved_at(self, client, db):
        incident = _seed_incident(db)

        response = client.patch(
            f"/api/v1/incidents/{incident.id}",
            json={"status": IncidentStatus.ACKNOWLEDGED.value},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == IncidentStatus.ACKNOWLEDGED.value
        assert body["resolved_at"] is None

    def test_patch_unknown_returns_404(self, client):
        response = client.patch(
            "/api/v1/incidents/999", json={"status": IncidentStatus.RESOLVED.value}
        )

        assert response.status_code == 404
        assert response.json()["code"] == "incident_not_found"

    def test_invalid_status_returns_422(self, client, db):
        incident = _seed_incident(db)

        response = client.patch(
            f"/api/v1/incidents/{incident.id}", json={"status": "bogus"}
        )

        assert response.status_code == 422
