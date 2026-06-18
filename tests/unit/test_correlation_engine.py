"""Unit tests for the CorrelationEngine (anomalies -> incidents)."""

from datetime import UTC, datetime, timedelta

from backend.app.core.config import Settings
from backend.app.correlation.correlation_engine import CorrelationEngine
from backend.app.models.anomaly import Anomaly
from backend.app.models.enums import IncidentStatus

_NOW = datetime(2026, 6, 18, 10, 0, 0, tzinfo=UTC)


def _settings():
    return Settings(_env_file=None, correlation_window_seconds=300)


def _anomaly(service="payment-api"):
    return Anomaly(
        strategy="z_score",
        service=service,
        signature=None,
        score=9.0,
        baseline_value=10.0,
        current_value=70.0,
        window_start=_NOW,
        window_end=_NOW,
    )


def _persist(db, anomalies):
    db.add_all(anomalies)
    db.commit()
    return anomalies


class TestCorrelationEngine:
    def test_no_anomalies_returns_none(self, db):
        assert CorrelationEngine(db, _settings()).correlate("payment-api", [], _NOW) is None

    def test_creates_incident(self, db):
        engine = CorrelationEngine(db, _settings())

        incident = engine.correlate("payment-api", _persist(db, [_anomaly()]), _NOW)

        assert incident is not None
        assert incident.status == IncidentStatus.OPEN.value
        assert len(incident.anomalies) == 1

    def test_absorbs_anomalies_within_window(self, db):
        engine = CorrelationEngine(db, _settings())
        first = engine.correlate("payment-api", _persist(db, [_anomaly()]), _NOW)

        second = engine.correlate(
            "payment-api", _persist(db, [_anomaly()]), _NOW + timedelta(seconds=60)
        )

        assert second.id == first.id
        assert len(second.anomalies) == 2

    def test_opens_new_incident_after_window(self, db):
        engine = CorrelationEngine(db, _settings())
        first = engine.correlate("payment-api", _persist(db, [_anomaly()]), _NOW)

        later = engine.correlate(
            "payment-api", _persist(db, [_anomaly()]), _NOW + timedelta(seconds=400)
        )

        assert later.id != first.id
