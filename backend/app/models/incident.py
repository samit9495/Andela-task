"""Incident ORM model. A correlated group of anomalies with a lifecycle."""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base
from backend.app.models.anomaly import Anomaly
from backend.app.models.enums import IncidentStatus


def _utcnow() -> datetime:
    return datetime.now(tz=UTC)


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255))
    service: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    severity: Mapped[str] = mapped_column(String(16), index=True)
    status: Mapped[str] = mapped_column(String(16), index=True, default=IncidentStatus.OPEN.value)
    root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    recommended_actions: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    runbook_references: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    anomalies: Mapped[list[Anomaly]] = relationship(back_populates="incident", order_by=Anomaly.id)
