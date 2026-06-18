"""Data access for events. Wraps SQLAlchemy queries; returns models or values."""

from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.models.event import Event


class EventRepository:
    """Persistence and queries for ``Event`` rows."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def add(self, event: Event) -> Event:
        self._db.add(event)
        return event

    def add_all(self, events: Sequence[Event]) -> list[Event]:
        self._db.add_all(events)
        return list(events)

    def list(
        self,
        *,
        service: str | None = None,
        level: str | None = None,
        since: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Event]:
        stmt = select(Event)
        if service is not None:
            stmt = stmt.where(Event.service == service)
        if level is not None:
            stmt = stmt.where(Event.level == level)
        if since is not None:
            stmt = stmt.where(Event.timestamp >= since)
        stmt = stmt.order_by(Event.timestamp.desc(), Event.id.desc()).limit(limit).offset(offset)
        return list(self._db.execute(stmt).scalars().all())

    def count(self) -> int:
        return self._db.execute(select(func.count()).select_from(Event)).scalar_one()

    def count_by_level(self) -> dict[str, int]:
        stmt = select(Event.level, func.count()).group_by(Event.level)
        return {row[0]: row[1] for row in self._db.execute(stmt).all()}

    def count_distinct_services(self) -> int:
        stmt = select(func.count(func.distinct(Event.service)))
        return self._db.execute(stmt).scalar_one()
