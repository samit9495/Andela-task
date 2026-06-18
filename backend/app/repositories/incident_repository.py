"""Data access for incidents."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.enums import IncidentStatus
from backend.app.models.incident import Incident


class IncidentRepository:
    """Persistence and queries for ``Incident`` rows."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def add(self, incident: Incident) -> Incident:
        self._db.add(incident)
        return incident

    def get(self, incident_id: int) -> Incident | None:
        return self._db.get(Incident, incident_id)

    def list_unresolved(self) -> list[Incident]:
        stmt = select(Incident).where(Incident.status != IncidentStatus.RESOLVED.value)
        return list(self._db.execute(stmt).scalars().all())

    def find_open_for_service(self, service: str, since: datetime) -> Incident | None:
        stmt = (
            select(Incident)
            .where(
                Incident.service == service,
                Incident.status != IncidentStatus.RESOLVED.value,
                Incident.updated_at >= since,
            )
            .order_by(Incident.updated_at.desc())
        )
        return self._db.execute(stmt).scalars().first()

    def list(
        self,
        *,
        status: str | None = None,
        severity: str | None = None,
    ) -> list[Incident]:
        stmt = select(Incident)
        if status is not None:
            stmt = stmt.where(Incident.status == status)
        if severity is not None:
            stmt = stmt.where(Incident.severity == severity)
        stmt = stmt.order_by(Incident.created_at.desc(), Incident.id.desc())
        return list(self._db.execute(stmt).scalars().all())
