"""Pydantic schemas for event ingestion and retrieval."""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.app.models.enums import LogLevel


class EventCreate(BaseModel):
    """Inbound log event. ``level`` is standardized during ingestion."""

    model_config = ConfigDict(extra="forbid")

    service: str = Field(min_length=1, max_length=255)
    level: str = Field(min_length=1, max_length=32)
    message: str = Field(min_length=1, max_length=4000)
    timestamp: datetime
    hostname: str | None = Field(default=None, max_length=255)
    environment: str | None = Field(default=None, max_length=64)
    metadata: dict[str, Any] | None = None

    @field_validator("timestamp")
    @classmethod
    def _require_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware (UTC)")
        return value.astimezone(UTC)


class EventRead(BaseModel):
    """Persisted event returned to clients."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    service: str
    level: LogLevel
    message: str
    signature: str
    timestamp: datetime
    hostname: str | None = None
    environment: str | None = None
    metadata: dict[str, Any] | None = Field(
        default=None, validation_alias="event_metadata", serialization_alias="metadata"
    )
    created_at: datetime


class BatchEventCreate(BaseModel):
    """A batch of events. Capped to protect the ingestion path."""

    model_config = ConfigDict(extra="forbid")

    events: list[EventCreate] = Field(min_length=1, max_length=1000)


class BatchEventResult(BaseModel):
    """Summary of a successful batch ingestion."""

    created: int
    event_ids: list[int]
