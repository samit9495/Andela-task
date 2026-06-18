"""Typed models mirroring the platform API schemas.

These intentionally mirror ``backend/app/schemas`` without importing them — the
SDK is a standalone package. Divergence from the backend contract is a bug.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EventCreate(BaseModel):
    """An inbound log event to ingest."""

    model_config = ConfigDict(extra="forbid")

    service: str = Field(min_length=1, max_length=255)
    level: str = Field(min_length=1, max_length=32)
    message: str = Field(min_length=1, max_length=4000)
    timestamp: datetime
    hostname: str | None = Field(default=None, max_length=255)
    environment: str | None = Field(default=None, max_length=64)
    metadata: dict[str, Any] | None = None


class EventRead(BaseModel):
    """A persisted event returned by the API."""

    id: int
    service: str
    level: str
    message: str
    signature: str
    timestamp: datetime
    hostname: str | None = None
    environment: str | None = None
    metadata: dict[str, Any] | None = None
    created_at: datetime


class BatchEventResult(BaseModel):
    """Summary of a successful batch ingestion."""

    created: int
    event_ids: list[int]


class AnomalyRead(BaseModel):
    id: int
    strategy: str
    service: str
    signature: str | None = None
    score: float
    baseline_value: float
    current_value: float
    window_start: datetime
    window_end: datetime
    created_at: datetime


class RunbookReference(BaseModel):
    slug: str
    title: str


class IncidentRead(BaseModel):
    id: int
    title: str
    service: str | None = None
    category: str | None = None
    severity: str
    status: str
    root_cause: str | None = None
    summary: str | None = None
    confidence_score: float | None = None
    recommended_actions: list[str] | None = None
    runbook_references: list[RunbookReference] | None = None
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None = None
    anomalies: list[AnomalyRead] = Field(default_factory=list)


class AlertRead(BaseModel):
    id: int
    incident_id: int
    channel: str
    status: str
    dedup_key: str
    payload: dict[str, Any]
    created_at: datetime


class RiskScore(BaseModel):
    score: float
    status: str
    error_penalty: float
    alert_penalty: float
    incident_penalty: float
