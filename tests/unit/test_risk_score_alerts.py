"""Risk score now reflects open alerts (Phase 4)."""

from datetime import UTC, datetime

from backend.app.models.alert import Alert
from backend.app.models.incident import Incident
from backend.app.risk.risk_score_service import RiskScoreService


def _incident_with_alert(db) -> None:
    incident = Incident(title="t", service="payment-api", severity="HIGH", status="OPEN")
    db.add(incident)
    db.commit()
    db.refresh(incident)
    db.add(
        Alert(
            incident_id=incident.id,
            channel="webhook",
            dedup_key=f"{incident.id}:webhook",
            payload={},
            created_at=datetime.now(tz=UTC),
        )
    )
    db.commit()


class TestRiskScoreWithAlerts:
    def test_alert_penalty_zero_when_no_alerts(self, db):
        result = RiskScoreService(db).calculate()

        assert result.alert_penalty == 0.0

    def test_alert_penalty_counts_distinct_incidents(self, db):
        _incident_with_alert(db)

        result = RiskScoreService(db).calculate()

        assert result.alert_penalty == 5.0
