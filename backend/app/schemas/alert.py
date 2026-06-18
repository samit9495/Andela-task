"""Schema for alert API responses."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AlertRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    incident_id: int
    channel: str
    status: str
    dedup_key: str
    payload: dict[str, Any]
    created_at: datetime
