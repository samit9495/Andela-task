"""Model round-trip and validation tests."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from watchdog_client.models import EventCreate, IncidentRead


def test_event_create_serializes_timestamp_to_json():
    event = EventCreate(
        service="payment-api",
        level="ERROR",
        message="boom",
        timestamp=datetime(2026, 6, 18, 10, 0, tzinfo=UTC),
    )

    dumped = event.model_dump(mode="json")

    assert dumped["service"] == "payment-api"
    assert dumped["timestamp"].startswith("2026-06-18T10:00:00")


def test_event_create_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        EventCreate(
            service="s",
            level="INFO",
            message="m",
            timestamp=datetime(2026, 6, 18, tzinfo=UTC),
            bogus="x",
        )


def test_incident_read_defaults_anomalies_to_empty_list():
    incident = IncidentRead(
        id=1,
        title="t",
        severity="LOW",
        status="OPEN",
        created_at=datetime(2026, 6, 18, tzinfo=UTC),
        updated_at=datetime(2026, 6, 18, tzinfo=UTC),
    )

    assert incident.anomalies == []
