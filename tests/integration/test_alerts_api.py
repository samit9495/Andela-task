"""Integration tests for the alerts API."""

from datetime import UTC, datetime

from backend.app.models.alert import Alert
from backend.app.models.incident import Incident


def _seed(db) -> int:
    incident = Incident(title="t", service="payment-api", severity="HIGH", status="OPEN")
    db.add(incident)
    db.commit()
    db.refresh(incident)
    db.add(
        Alert(
            incident_id=incident.id,
            channel="webhook",
            dedup_key=f"{incident.id}:webhook",
            payload={"incident_id": incident.id, "severity": "HIGH"},
            created_at=datetime.now(tz=UTC),
        )
    )
    db.commit()
    return incident.id


class TestAlertsApi:
    def test_list_alerts_returns_fired_alerts(self, client, db):
        _seed(db)

        response = client.get("/api/v1/alerts")

        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert body[0]["channel"] == "webhook"

    def test_filter_by_incident(self, client, db):
        incident_id = _seed(db)

        response = client.get("/api/v1/alerts", params={"incident_id": incident_id})

        assert response.status_code == 200
        assert all(a["incident_id"] == incident_id for a in response.json())
