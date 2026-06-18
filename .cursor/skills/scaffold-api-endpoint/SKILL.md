---
name: scaffold-api-endpoint
description: Scaffold a new FastAPI endpoint test-first — Pydantic schemas, service injection, APIRouter, response_model, and pytest coverage. Use when creating any new REST endpoint.
---

# Scaffold FastAPI Endpoint (Test-First)

## Trigger

Use when asked to: create endpoint, add API route, new REST endpoint, new FastAPI route, expose a resource.

## Context

Every endpoint in this project follows the same shape: thin route → service → repository → model. Every endpoint is built test-first per `.cursor/rules/andela-tdd-discipline.mdc`.

The example below scaffolds the `Event` ingestion endpoint — adapt to the resource you are building.

## Step 0 — Write the failing test first (RED)

```python
# tests/integration/test_events_api.py
from fastapi import status

class TestEventsAPI:
    def test_create_event_returns_201_with_persisted_row(self, client, db):
        payload = {
            "service": "payment-api",
            "level": "ERROR",
            "message": "Database timeout after 20 seconds",
            "timestamp": "2026-06-18T10:00:00Z",
        }
        resp = client.post("/api/v1/events", json=payload)
        assert resp.status_code == status.HTTP_201_CREATED
        body = resp.json()
        assert body["id"] > 0
        assert body["service"] == "payment-api"
        assert body["level"] == "ERROR"
```

Run it. Confirm 404 / import error. Commit with `test: ...`.

## Step 1 — Pydantic schemas

```python
# backend/app/schemas/event.py
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field


class LogLevel(str, Enum):
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class EventBase(BaseModel):
    service: str = Field(min_length=1, max_length=100)
    level: LogLevel
    message: str = Field(min_length=1, max_length=4000)
    timestamp: datetime
    hostname: str | None = Field(default=None, max_length=255)
    environment: str | None = Field(default=None, max_length=50)
    metadata: dict | None = None


class EventCreate(EventBase):
    pass


class EventRead(EventBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    signature: str
```

## Step 2 — Repository (data access only)

```python
# backend/app/repositories/event_repository.py
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.event import Event


class EventRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, event: Event) -> Event:
        self.db.add(event)
        self.db.flush()
        return event

    def list(
        self,
        service: str | None,
        level: str | None,
        limit: int,
        offset: int,
    ) -> list[Event]:
        stmt = select(Event).order_by(Event.timestamp.desc()).limit(limit).offset(offset)
        if service is not None:
            stmt = stmt.where(Event.service == service)
        if level is not None:
            stmt = stmt.where(Event.level == level)
        return list(self.db.scalars(stmt))
```

## Step 3 — Service (use cases)

```python
# backend/app/ingestion/ingestion_service.py
from sqlalchemy.orm import Session
from app.models.event import Event
from app.repositories.event_repository import EventRepository
from app.schemas.event import EventCreate
from app.ingestion.normalizer import normalize_message


class IngestionService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = EventRepository(db)

    def ingest(self, payload: EventCreate) -> Event:
        event = Event(
            service=payload.service,
            level=payload.level.value,
            message=payload.message,
            signature=normalize_message(payload.message),
            timestamp=payload.timestamp,
            hostname=payload.hostname,
            environment=payload.environment,
            metadata_json=payload.metadata,
        )
        self.repo.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event
```

## Step 4 — Route (thin)

```python
# backend/app/api/routes/events.py
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.event import EventCreate, EventRead
from app.ingestion.ingestion_service import IngestionService

router = APIRouter(prefix="/api/v1/events", tags=["events"])


@router.post("", response_model=EventRead, status_code=status.HTTP_201_CREATED)
def create_event(
    payload: EventCreate,
    db: Session = Depends(get_db),
) -> EventRead:
    event = IngestionService(db).ingest(payload)
    return EventRead.model_validate(event)
```

Include the router in `backend/app/main.py`:

```python
from app.api.routes import events
app.include_router(events.router)
```

## Step 5 — Make the test green

Run the test. Fix the smallest thing until green. Paste the pass.

## Step 6 — Commit GREEN

```bash
git add backend/app/api/routes/events.py backend/app/schemas/event.py \
        backend/app/ingestion/ingestion_service.py \
        backend/app/repositories/event_repository.py \
        backend/app/models/event.py backend/app/main.py
git commit -m "feat: implement POST /api/v1/events endpoint"
```

## Step 7 — Add the next RED for the next behavior

Next behaviors to test, one per cycle:

- `test_create_event_with_invalid_level_returns_422`
- `test_create_event_with_missing_required_field_returns_422`
- `test_create_event_with_message_over_limit_returns_422`
- `test_create_event_batch_accepts_up_to_1000_events`
- `test_create_event_batch_rejects_over_1000_events`
- `test_list_events_filters_by_service_and_level`
- `test_list_events_paginates_with_limit_and_offset`

Each one drives a small RED → GREEN → REFACTOR triple.

## Checklist

- [ ] Failing integration test first (RED), committed as `test: ...`
- [ ] Pydantic schemas: separate Create / Read; Enums for fixed sets
- [ ] Repository methods are query-only, return models or values
- [ ] Service holds the use case; depends on the repo via constructor
- [ ] Route uses `Depends(get_db)`, declares `response_model=` and `status_code=`
- [ ] Domain exceptions raised in the service map to HTTP via handlers
- [ ] Tests cover happy path, validation, edge cases (max-size, missing field, batch limits)
- [ ] No secrets, no hardcoded URLs

## See also

- `.cursor/skills/andela-tdd-loop/SKILL.md` — exact RED→GREEN→REFACTOR steps
- `.cursor/skills/scaffold-service-layer/SKILL.md` — when the service needs more than CRUD
- `.cursor/rules/andela-api-routes.mdc`, `.cursor/rules/andela-fastapi-core.mdc`, `.cursor/rules/andela-security.mdc`
