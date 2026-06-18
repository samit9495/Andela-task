"""Schemas for anomalies and incidents."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from backend.app.models.enums import IncidentStatus, Severity


class RunbookReferenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slug: str
    title: str


class AnomalyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    strategy: str
    service: str
    signature: str | None
    score: float
    baseline_value: float
    current_value: float
    window_start: datetime
    window_end: datetime
    created_at: datetime


class IncidentStatusUpdate(BaseModel):
    """Body for ``PATCH /api/v1/incidents/{id}`` status transitions."""

    model_config = ConfigDict(extra="forbid")

    status: IncidentStatus


class IncidentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    service: str | None
    category: str | None
    severity: Severity
    status: IncidentStatus
    root_cause: str | None
    summary: str | None
    confidence_score: float | None
    recommended_actions: list[str] | None
    runbook_references: list[RunbookReferenceRead] | None
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None
    anomalies: list[AnomalyRead]
