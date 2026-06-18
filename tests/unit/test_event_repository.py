"""Unit tests for EventRepository (persistence, filters, aggregations)."""

from datetime import UTC, datetime, timedelta

from backend.app.models.event import Event
from backend.app.repositories.event_repository import EventRepository

_BASE = datetime(2026, 6, 18, 10, 0, 0, tzinfo=UTC)


def _event(service="payment-api", level="ERROR", message="Database timeout", offset_min=0):
    return Event(
        service=service,
        level=level,
        message=message,
        signature=message,
        timestamp=_BASE + timedelta(minutes=offset_min),
    )


class TestEventRepository:
    def test_add_persists_and_assigns_id(self, db):
        repo = EventRepository(db)

        stored = repo.add(_event())
        db.flush()

        assert stored.id is not None

    def test_add_all_persists_many(self, db):
        repo = EventRepository(db)

        stored = repo.add_all([_event(), _event(message="Connection refused")])
        db.flush()

        assert len(stored) == 2

    def test_list_returns_all_by_default(self, db):
        repo = EventRepository(db)
        repo.add_all([_event(), _event(service="auth-api")])
        db.flush()

        assert len(repo.list()) == 2

    def test_list_filters_by_service(self, db):
        repo = EventRepository(db)
        repo.add_all([_event(service="payment-api"), _event(service="auth-api")])
        db.flush()

        results = repo.list(service="auth-api")

        assert [e.service for e in results] == ["auth-api"]

    def test_list_filters_by_level(self, db):
        repo = EventRepository(db)
        repo.add_all([_event(level="ERROR"), _event(level="INFO")])
        db.flush()

        results = repo.list(level="INFO")

        assert [e.level for e in results] == ["INFO"]

    def test_list_filters_by_since(self, db):
        repo = EventRepository(db)
        repo.add_all([_event(offset_min=0), _event(offset_min=10)])
        db.flush()

        results = repo.list(since=_BASE + timedelta(minutes=5))

        assert len(results) == 1

    def test_list_applies_limit_and_offset(self, db):
        repo = EventRepository(db)
        repo.add_all([_event(offset_min=i) for i in range(5)])
        db.flush()

        page = repo.list(limit=2, offset=2)

        assert len(page) == 2

    def test_list_empty_returns_empty_list(self, db):
        assert EventRepository(db).list() == []

    def test_count(self, db):
        repo = EventRepository(db)
        repo.add_all([_event(), _event()])
        db.flush()

        assert repo.count() == 2

    def test_count_by_level(self, db):
        repo = EventRepository(db)
        repo.add_all([_event(level="ERROR"), _event(level="ERROR"), _event(level="INFO")])
        db.flush()

        assert repo.count_by_level() == {"ERROR": 2, "INFO": 1}

    def test_count_distinct_services(self, db):
        repo = EventRepository(db)
        repo.add_all([_event(service="a"), _event(service="a"), _event(service="b")])
        db.flush()

        assert repo.count_distinct_services() == 2
