"""Data access for alerts."""

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.models.alert import Alert


class AlertRepository:
    """Persistence and queries for ``Alert`` rows."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def add(self, alert: Alert) -> Alert:
        self._db.add(alert)
        return alert

    def exists_since(self, dedup_key: str, since: datetime) -> bool:
        stmt = select(Alert.id).where(Alert.dedup_key == dedup_key, Alert.created_at >= since)
        return self._db.execute(stmt).first() is not None

    def count(self) -> int:
        return int(self._db.execute(select(func.count(Alert.id))).scalar_one())

    def count_distinct_incidents(self) -> int:
        stmt = select(func.count(func.distinct(Alert.incident_id)))
        return int(self._db.execute(stmt).scalar_one())

    def list(self, *, incident_id: int | None = None) -> list[Alert]:
        stmt = select(Alert)
        if incident_id is not None:
            stmt = stmt.where(Alert.incident_id == incident_id)
        stmt = stmt.order_by(Alert.created_at.desc(), Alert.id.desc())
        return list(self._db.execute(stmt).scalars().all())
