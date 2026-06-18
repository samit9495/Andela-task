"""Integration tests for the risk-score API."""

from datetime import UTC, datetime

from backend.app.incidents.incident_service import IncidentService
from backend.app.models.anomaly import Anomaly
from backend.app.models.event import Event


class TestRiskScoreApi:
    def test_healthy_when_empty(self, client):
        response = client.get("/api/v1/risk-score")

        assert response.status_code == 200
        body = response.json()
        assert body["score"] == 100.0
        assert body["status"] == "Healthy"

    def test_reflects_errors_and_incidents(self, client, db):
        # Risk score windows events; use wall-clock now so the events fall inside.
        now = datetime.now(tz=UTC)
        db.add_all(
            [
                Event(
                    service="payment-api",
                    level=level,
                    message="m",
                    signature="m",
                    timestamp=now,
                )
                for level in (["INFO"] * 8 + ["ERROR"] * 2)
            ]
        )
        anomalies = [
            Anomaly(
                strategy="z_score",
                service="payment-api",
                signature=None,
                score=9.0,
                baseline_value=1.0,
                current_value=9.0,
                window_start=now,
                window_end=now,
            )
            for _ in range(2)
        ]
        db.add_all(anomalies)
        db.commit()
        IncidentService(db).open_incident("payment-api", anomalies, now)

        response = client.get("/api/v1/risk-score")

        body = response.json()
        assert body["error_penalty"] == 16.0
        assert body["incident_penalty"] == 6.0
        assert body["score"] == 78.0
        assert body["status"] == "Warning"
