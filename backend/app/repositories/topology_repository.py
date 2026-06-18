"""Data access for the service topology graph."""

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.models.service_topology import ServiceTopology


class ServiceTopologyRepository:
    """Persistence and queries for ``ServiceTopology`` rows."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def upsert(self, service: str, depends_on: list[str]) -> ServiceTopology:
        existing = self._db.execute(
            select(ServiceTopology).where(ServiceTopology.service == service)
        ).scalar_one_or_none()
        if existing is not None:
            existing.depends_on = list(depends_on)
            existing.updated_at = datetime.now(tz=UTC)
            return existing
        row = ServiceTopology(service=service, depends_on=list(depends_on))
        self._db.add(row)
        return row

    def adjacency(self) -> dict[str, list[str]]:
        rows = self._db.execute(select(ServiceTopology)).scalars().all()
        return {row.service: list(row.depends_on) for row in rows}

    def count(self) -> int:
        return int(self._db.execute(select(func.count(ServiceTopology.id))).scalar_one())
