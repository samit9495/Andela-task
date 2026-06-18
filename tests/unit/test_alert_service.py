"""Unit tests for the AlertService (fan-out, dedup, rate-limit)."""

from datetime import UTC, datetime, timedelta

from backend.app.alerts.alert_service import AlertService
from backend.app.alerts.channels.base import AlertChannel
from backend.app.models.incident import Incident
from backend.app.repositories.alert_repository import AlertRepository


class _RecordingChannel:
    def __init__(self, name: str) -> None:
        self.name = name
        self.sent: list[dict] = []

    def send(self, payload: dict) -> None:
        self.sent.append(payload)


def _incident(db) -> Incident:
    incident = Incident(
        title="DB degradation", service="payment-api", severity="CRITICAL", status="OPEN"
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident


def _service(db, channels: list[AlertChannel]) -> AlertService:
    return AlertService(db, channels=channels, rate_limit_seconds=300)


class TestAlertService:
    def test_fans_out_to_all_channels(self, db):
        incident = _incident(db)
        channels = [_RecordingChannel("webhook"), _RecordingChannel("email")]
        service = _service(db, channels)

        alerts = service.raise_for_incident(incident, now=datetime.now(tz=UTC))

        assert {a.channel for a in alerts} == {"webhook", "email"}
        assert all(len(c.sent) == 1 for c in channels)
        assert AlertRepository(db).count_distinct_incidents() == 1

    def test_payload_includes_incident_fields_but_not_raw_messages(self, db):
        incident = _incident(db)
        channel = _RecordingChannel("webhook")
        service = _service(db, [channel])

        service.raise_for_incident(incident, now=datetime.now(tz=UTC))

        payload = channel.sent[0]
        assert payload["incident_id"] == incident.id
        assert payload["severity"] == "CRITICAL"
        assert payload["service"] == "payment-api"

    def test_dedup_suppresses_repeat_within_window(self, db):
        incident = _incident(db)
        channel = _RecordingChannel("webhook")
        service = _service(db, [channel])
        now = datetime.now(tz=UTC)

        first = service.raise_for_incident(incident, now=now)
        second = service.raise_for_incident(incident, now=now + timedelta(seconds=60))

        assert len(first) == 1
        assert second == []
        assert len(channel.sent) == 1

    def test_fires_again_after_rate_limit_window(self, db):
        incident = _incident(db)
        channel = _RecordingChannel("webhook")
        service = _service(db, [channel])
        now = datetime.now(tz=UTC)

        service.raise_for_incident(incident, now=now)
        later = service.raise_for_incident(incident, now=now + timedelta(seconds=400))

        assert len(later) == 1
        assert len(channel.sent) == 2
