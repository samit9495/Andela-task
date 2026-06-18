"""Metrics endpoint. Aggregates events, incidents, alerts, and the risk score."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.repositories.alert_repository import AlertRepository
from backend.app.repositories.event_repository import EventRepository
from backend.app.repositories.incident_repository import IncidentRepository
from backend.app.risk.risk_score_service import RiskScoreService
from backend.app.schemas.metrics import MetricsResponse

router = APIRouter(tags=["metrics"])


@router.get("/metrics", response_model=MetricsResponse)
def get_metrics(db: Session = Depends(get_db)) -> MetricsResponse:
    events = EventRepository(db)
    return MetricsResponse(
        total_events=events.count(),
        events_by_level=events.count_by_level(),
        monitored_services=events.count_distinct_services(),
        total_incidents=IncidentRepository(db).count(),
        total_alerts=AlertRepository(db).count(),
        risk_score=RiskScoreService(db).calculate().score,
    )
