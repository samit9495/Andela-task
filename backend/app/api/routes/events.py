"""Event ingestion and retrieval endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query, status

from backend.app.api.deps import get_event_repository, get_ingestion_service
from backend.app.ingestion.ingestion_service import IngestionService
from backend.app.ingestion.normalizer import normalize_level
from backend.app.repositories.event_repository import EventRepository
from backend.app.schemas.event import (
    BatchEventCreate,
    BatchEventResult,
    EventCreate,
    EventRead,
)

router = APIRouter(prefix="/api/v1", tags=["events"])


@router.post("/events", response_model=EventRead, status_code=status.HTTP_201_CREATED)
def create_event(
    payload: EventCreate,
    ingestion: IngestionService = Depends(get_ingestion_service),
) -> EventRead:
    event = ingestion.ingest_event(payload)
    return EventRead.model_validate(event)


@router.post(
    "/events/batch",
    response_model=BatchEventResult,
    status_code=status.HTTP_201_CREATED,
)
def create_events_batch(
    payload: BatchEventCreate,
    ingestion: IngestionService = Depends(get_ingestion_service),
) -> BatchEventResult:
    events = ingestion.ingest_batch(payload.events)
    return BatchEventResult(created=len(events), event_ids=[event.id for event in events])


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
