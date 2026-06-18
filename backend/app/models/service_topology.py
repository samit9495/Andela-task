"""ServiceTopology ORM model. A service and the services it depends on."""

from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


def _utcnow() -> datetime:
    return datetime.now(tz=UTC)


class ServiceTopology(Base):
    __tablename__ = "service_topology"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    service: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    depends_on: Mapped[list[str]] = mapped_column(JSON, default=list)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
