"""Unit tests for RiskScoreService (penalties, clamping, bands)."""

from datetime import UTC, datetime

from backend.app.incidents.incident_service import IncidentService
from backend.app.models.anomaly import Anomaly
from backend.app.models.event import Event
from backend.app.risk.risk_score_service import RiskScoreService

_NOW = datetime(2026, 6, 18, 10, 0, 0, tzinfo=UTC)


def _event(level="INFO"):
    return Event(
        service="payment-api",
        level=level,
        message="msg",
        signature="msg",
        timestamp=_NOW,
    )


def _anomaly():
    return Anomaly(
        strategy="z_score",
        service="payment-api",
        signature=None,
        score=9.0,
        baseline_value=10.0,
        current_value=70.0,
        window_start=_NOW,
        window_end=_NOW,
    )


class TestRiskScoreService:
    def test_healthy_when_no_events_or_incidents(self, db):
        result = RiskScoreService(db).calculate()

        assert result.score == 100.0
        assert result.status == "Healthy"
        assert result.error_penalty == 0.0
        assert result.incident_penalty == 0.0

    def test_penalties_reduce_score(self, db):
        db.add_all([_event() for _ in range(8)] + [_event("ERROR") for _ in range(2)])
        anomalies = [_anomaly(), _anomaly()]
        db.add_all(anomalies)
        db.commit()
        IncidentService(db).open_incident("payment-api", anomalies, _NOW)  # MEDIUM -> 6

        result = RiskScoreService(db).calculate()

        assert result.error_penalty == 16.0  # 20% error rate * 0.8
        assert result.incident_penalty == 6.0
        assert result.score == 78.0
        assert result.status == "Warning"
