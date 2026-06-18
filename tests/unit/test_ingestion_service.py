"""Unit tests for IngestionService (normalize + persist)."""

from datetime import UTC, datetime

import pytest
from backend.app.core.exceptions import EventValidationError
from backend.app.ingestion.ingestion_service import IngestionService
from backend.app.schemas.event import EventCreate

_TS = datetime(2026, 6, 18, 10, 0, 0, tzinfo=UTC)


def _payload(level="warning", message="Latency 12 ms after restart", **kwargs):
    return EventCreate(service="payment-api", level=level, message=message, timestamp=_TS, **kwargs)


class TestIngestionService:
    def test_ingest_event_computes_signature_and_canonical_level(self, db):
        service = IngestionService(db)

        stored = service.ingest_event(_payload())

        assert stored.id is not None
        assert stored.level == "WARN"
        assert stored.signature == "Latency <NUM> ms after restart"

    def test_ingest_event_preserves_optional_fields(self, db):
        service = IngestionService(db)

        stored = service.ingest_event(_payload(hostname="host-1", metadata={"region": "us"}))

        assert stored.hostname == "host-1"
        assert stored.event_metadata == {"region": "us"}

    def test_ingest_batch_persists_all(self, db):
        service = IngestionService(db)

        stored = service.ingest_batch([_payload(), _payload(message="Connection refused")])

        assert len(stored) == 2
        assert all(e.id is not None for e in stored)

    def test_ingest_unknown_level_raises(self, db):
        service = IngestionService(db)

        with pytest.raises(EventValidationError):
            service.ingest_event(_payload(level="bananas"))
