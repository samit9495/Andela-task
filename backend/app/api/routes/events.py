"""Event ingestion and retrieval endpoints."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query, status

from backend.app.api.deps import (
    get_event_repository,
    get_ingestion_service,
    get_pipeline_service,
)
from backend.app.ingestion.ingestion_service import IngestionService
from backend.app.ingestion.normalizer import normalize_level
from backend.app.models.event import Event
from backend.app.pipeline.pipeline_service import PipelineService
from backend.app.repositories.event_repository import EventRepository
from backend.app.schemas.event import (
    BatchEventCreate,
    BatchEventResult,
    EventCreate,
    EventRead,
)

router = APIRouter(prefix="/api/v1", tags=["events"])


def _run_pipeline(pipeline: PipelineService, events: list[Event]) -> None:
    """Run detection -> correlation -> triage -> alert for each affected service."""
    services = {event.service for event in events}
    if services:
        pipeline.process_services(services, now=datetime.now(tz=UTC))


@router.post("/events", response_model=EventRead, status_code=status.HTTP_201_CREATED)
def create_event(
    payload: EventCreate,
    ingestion: IngestionService = Depends(get_ingestion_service),
    pipeline: PipelineService = Depends(get_pipeline_service),
) -> EventRead:
    event = ingestion.ingest_event(payload)
    response = EventRead.model_validate(event)
    _run_pipeline(pipeline, [event])
    return response


@router.post(
    "/events/batch",
    response_model=BatchEventResult,
    status_code=status.HTTP_201_CREATED,
)
def create_events_batch(
    payload: BatchEventCreate,
    ingestion: IngestionService = Depends(get_ingestion_service),
    pipeline: PipelineService = Depends(get_pipeline_service),
) -> BatchEventResult:
    events = ingestion.ingest_batch(payload.events)
    result = BatchEventResult(created=len(events), event_ids=[event.id for event in events])
    _run_pipeline(pipeline, events)
    return result


@router.get("/events", response_model=list[EventRead])
def list_events(
    service: str | None = Query(default=None, max_length=255),
    level: str | None = Query(default=None, max_length=32),
    since: datetime | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    repo: EventRepository = Depends(get_event_repository),
) -> list[EventRead]:
    normalized_level = normalize_level(level).value if level is not None else None
    events = repo.list(
        service=service,
        level=normalized_level,
        since=since,
        limit=limit,
        offset=offset,
    )
    return [EventRead.model_validate(event) for event in events]
