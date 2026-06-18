"""Pydantic schema for the metrics endpoint."""

from pydantic import BaseModel


class MetricsResponse(BaseModel):
    """Platform metrics. Event-centric in Phase 1; expanded in later phases."""

    total_events: int
    events_by_level: dict[str, int]
    monitored_services: int
    total_incidents: int
    total_alerts: int
    risk_score: float
