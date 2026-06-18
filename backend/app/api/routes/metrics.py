"""Metrics endpoint. Event-centric in Phase 1; expanded in later phases."""

from fastapi import APIRouter, Depends

from backend.app.api.deps import get_event_repository
from backend.app.repositories.event_repository import EventRepository
from backend.app.schemas.metrics import MetricsResponse

router = APIRouter(tags=["metrics"])


@router.get("/metrics", response_model=MetricsResponse)
def get_metrics(
    repo: EventRepository = Depends(get_event_repository),
) -> MetricsResponse:
    return MetricsResponse(
        total_events=repo.count(),
        events_by_level=repo.count_by_level(),
        monitored_services=repo.count_distinct_services(),
    )
