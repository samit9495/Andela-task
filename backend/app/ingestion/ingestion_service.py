"""Ingestion use cases: normalize inbound events and persist them.

The service owns the transaction boundary (one service call = one commit).
"""

from sqlalchemy.orm import Session

from backend.app.ingestion.normalizer import generate_signature, normalize_level
from backend.app.models.event import Event
from backend.app.repositories.event_repository import EventRepository
from backend.app.schemas.event import EventCreate


class IngestionService:
    """Validate, normalize, and persist log events."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._repo = EventRepository(db)

    def ingest_event(self, payload: EventCreate) -> Event:
        event = self._to_model(payload)
        self._repo.add(event)
        self._db.commit()
        self._db.refresh(event)
        return event

    def ingest_batch(self, payloads: list[EventCreate]) -> list[Event]:
        events = [self._to_model(payload) for payload in payloads]
        self._repo.add_all(events)
        self._db.commit()
        for event in events:
            self._db.refresh(event)
        return events

    def _to_model(self, payload: EventCreate) -> Event:
        return Event(
            service=payload.service,
            level=normalize_level(payload.level).value,
            message=payload.message,
            signature=generate_signature(payload.message),
            timestamp=payload.timestamp,
            hostname=payload.hostname,
            environment=payload.environment,
            event_metadata=payload.metadata,
        )
