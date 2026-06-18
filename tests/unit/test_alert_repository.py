"""Unit tests for the AlertRepository."""

from datetime import UTC, datetime, timedelta

from backend.app.models.alert import Alert
from backend.app.models.incident import Incident
from backend.app.repositories.alert_repository import AlertRepository


def _incident(db) -> Incident:
    incident = Incident(title="t", service="svc", severity="HIGH", status="OPEN")
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident


def _alert(incident_id: int, *, channel: str, dedup_key: str, created_at: datetime) -> Alert:
    return Alert(
        incident_id=incident_id,
        channel=channel,
        dedup_key=dedup_key,
        payload={"k": "v"},
        created_at=created_at,
    )


class TestAlertRepository:
    def test_add_and_list(self, db):
        incident = _incident(db)
        now = datetime.now(tz=UTC)
        repo = AlertRepository(db)
        repo.add(_alert(incident.id, channel="webhook", dedup_key="k1", created_at=now))
        db.commit()

        alerts = repo.list()

        assert len(alerts) == 1
        assert alerts[0].channel == "webhook"

    def test_exists_since_window(self, db):
        incident = _incident(db)
        now = datetime.now(tz=UTC)
        repo = AlertRepository(db)
        created = now - timedelta(seconds=60)
        repo.add(_alert(incident.id, channel="webhook", dedup_key="dk", created_at=created))
        db.commit()

        assert repo.exists_since("dk", now - timedelta(seconds=120)) is True
        assert repo.exists_since("dk", now - timedelta(seconds=30)) is False

    def test_count_distinct_incidents(self, db):
        first = _incident(db)
        second = _incident(db)
        now = datetime.now(tz=UTC)
        repo = AlertRepository(db)
        repo.add(_alert(first.id, channel="webhook", dedup_key="a", created_at=now))
        repo.add(_alert(first.id, channel="email", dedup_key="b", created_at=now))
        repo.add(_alert(second.id, channel="webhook", dedup_key="c", created_at=now))
        db.commit()

        assert repo.count_distinct_incidents() == 2

    def test_list_filters_by_incident(self, db):
        first = _incident(db)
        second = _incident(db)
        now = datetime.now(tz=UTC)
        repo = AlertRepository(db)
        repo.add(_alert(first.id, channel="webhook", dedup_key="a", created_at=now))
        repo.add(_alert(second.id, channel="webhook", dedup_key="c", created_at=now))
        db.commit()

        assert len(repo.list(incident_id=first.id)) == 1
