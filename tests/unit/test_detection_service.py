"""Integration-style unit tests for DetectionService (events -> anomalies)."""

from datetime import UTC, datetime, timedelta

from backend.app.core.config import Settings
from backend.app.detection.detection_service import DetectionService
from backend.app.models.event import Event

_NOW = datetime(2026, 6, 18, 10, 0, 0, tzinfo=UTC)


def _settings():
    return Settings(
        _env_file=None,
        min_baseline_samples=3,
        detection_bucket_seconds=60,
        signature_burst_floor=5,
        signature_burst_multiplier=5.0,
    )


def _seed_spike(db):
    events = []
    # Baseline buckets: one event per prior minute.
    for minute in (1, 2, 3):
        events.append(_event(_NOW - timedelta(seconds=minute * 60 + 1)))
    # Current bucket: a burst.
    for _ in range(20):
        events.append(_event(_NOW - timedelta(seconds=1)))
    db.add_all(events)
    db.commit()


def _event(ts):
    return Event(
        service="payment-api",
        level="ERROR",
        message="Database timeout",
        signature="Database timeout",
        timestamp=ts,
    )


class TestDetectionService:
    def test_detects_signature_burst_and_persists(self, db):
        _seed_spike(db)
        service = DetectionService(db, _settings())

        anomalies = service.analyze_service("payment-api", _NOW)

        assert len(anomalies) >= 1
        assert any(a.strategy == "signature_frequency" for a in anomalies)
        assert all(a.id is not None for a in anomalies)

    def test_rerun_does_not_duplicate(self, db):
        _seed_spike(db)
        service = DetectionService(db, _settings())
        service.analyze_service("payment-api", _NOW)

        second_run = service.analyze_service("payment-api", _NOW)

        assert second_run == []

    def test_no_anomalies_for_quiet_service(self, db):
        db.add(_event(_NOW - timedelta(seconds=1)))
        db.commit()
        service = DetectionService(db, _settings())

        assert service.analyze_service("payment-api", _NOW) == []
