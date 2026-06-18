"""Unit tests for RiskScoreService (penalties, clamping, bands)."""

from datetime import UTC, datetime, timedelta

from backend.app.incidents.incident_service import IncidentService
from backend.app.models.anomaly import Anomaly
from backend.app.models.event import Event
from backend.app.risk.risk_score_service import RiskScoreService

_NOW = datetime(2026, 6, 18, 10, 0, 0, tzinfo=UTC)


def _event(level="INFO", timestamp=None):
    return Event(
        service="payment-api",
        level=level,
        message="msg",
        signature="msg",
        timestamp=timestamp or _NOW,
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

        result = RiskScoreService(db).calculate(now=_NOW)

        assert result.error_penalty == 16.0  # 20% error rate * 0.8
        assert result.incident_penalty == 6.0
        assert result.score == 78.0
        assert result.status == "Warning"

    def test_error_rate_uses_only_events_inside_the_window(self, db):
        """Old INFO must not dilute a recent ERROR spike (MASTER_PLAN section 26.3)."""
        long_ago = _NOW - timedelta(hours=2)
        db.add_all([_event(timestamp=long_ago) for _ in range(1000)])
        # Inside the default 15-min window: 6 ERROR + 4 INFO -> 60% error rate.
        db.add_all(
            [_event("ERROR", timestamp=_NOW) for _ in range(6)]
            + [_event(timestamp=_NOW) for _ in range(4)]
        )
        db.commit()

        result = RiskScoreService(db).calculate(now=_NOW)

        # 60% * 0.8 = 48 -> capped at the documented 40.
        assert result.error_penalty == 40.0
