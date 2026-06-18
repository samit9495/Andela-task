---
name: scaffold-service-layer
description: Scaffold a service class test-first — constructor-injected Session and dependencies, repository delegation, domain exceptions, structured return. Use when extracting business logic out of a route or adding a new use case.
---

# Scaffold Service Layer (Test-First)

## Trigger

Use when asked to: create service, extract service, new use case, move logic out of a route, add an engine (detection, correlation, triage, alert, risk).

## Context

Services are where business logic lives. They:

- Receive a `Session` (and optionally a clock / id generator / `LLMClient`) via constructor injection.
- Compose repositories and engines.
- Raise domain exceptions (not `HTTPException`).
- Commit at the boundary of a single use case.

The Correlation Engine is a good example — it walks anomalies and groups them into incidents, so it lives at the service layer.

## Step 0 — Write the failing unit test first (RED)

```python
# tests/unit/test_correlation_engine.py
from datetime import datetime, timedelta, timezone
from app.correlation.correlation_engine import CorrelationEngine
from app.models.anomaly import Anomaly


class TestCorrelationEngine:
    def test_groups_anomalies_within_window_into_one_incident(self, db):
        engine = CorrelationEngine(db, window=timedelta(minutes=5))
        now = datetime(2026, 6, 18, 10, 0, tzinfo=timezone.utc)
        anomalies = [
            Anomaly(service="payment-api", signature="db_timeout",
                    detected_at=now, strategy="z_score"),
            Anomaly(service="payment-api", signature="connection_refused",
                    detected_at=now + timedelta(minutes=1), strategy="signature_frequency"),
        ]
        incidents = engine.correlate(anomalies)
        assert len(incidents) == 1
        assert len(incidents[0].anomalies) == 2

    def test_separate_services_become_separate_incidents(self, db):
        ...
```

Run each test individually as you go through the loop. One RED per behavior. Commit each.

## Step 1 — The service skeleton

```python
# backend/app/correlation/correlation_engine.py
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.anomaly import Anomaly
from app.models.incident import Incident


class CorrelationEngine:
    """Groups related anomalies into incidents.

    No HTTP, no Pydantic — pure logic that operates on a Session and a list
    of Anomaly rows. Keeps the alert engine deduplicated.
    """

    def __init__(self, db: Session, window: timedelta) -> None:
        self.db = db
        self.window = window

    def correlate(self, anomalies: list[Anomaly]) -> list[Incident]:
        # group anomalies by (service, time-bucket); produce one Incident per group
        ...
```

## Step 2 — Compose into a route or pipeline (later, separate commit)

The triage pipeline service composes ingestion → detection → correlation → triage:

```python
# backend/app/incidents/incident_service.py
class IncidentService:
    def __init__(self, db: Session, llm: LLMClient) -> None:
        self.detection = DetectionEngine(default_detectors())
        self.correlation = CorrelationEngine(db, window=timedelta(minutes=5))
        self.triage = TriageService(db, llm)
```

Each composition step is its own RED → GREEN cycle.

## Step 3 — Domain exceptions for negative cases

```python
# backend/app/core/exceptions.py
class IncidentNotFound(DomainError):
    def __init__(self, incident_id: int):
        super().__init__(f"incident {incident_id} not found")
        self.incident_id = incident_id
```

Mapped to 404 by an exception handler in `backend/app/main.py`.

## Step 4 — Transactions

If the service does a multi-statement write:

```python
def open_incident(self, anomalies: list[Anomaly]) -> Incident:
    with self.db.begin():
        incident = Incident(...)
        self.db.add(incident)
        for a in anomalies:
            a.incident_id = incident.id
    self.db.refresh(incident)
    return incident
```

For aggregations / classification (read-only) no explicit transaction is needed.

## Step 5 — When to introduce a Repository

Inline `select(...)` is fine for the first one or two queries. Extract a repository when:

- More than three query helpers exist in the service.
- The same query is called from two services (e.g., both `IncidentService` and `RiskScoreService` need active-incident counts).
- You want to swap the data access for a unit test that is genuinely about the use case, not the SQL.

## Step 6 — Inject the LLM client (for triage services)

```python
class TriageService:
    def __init__(self, db: Session, llm: LLMClient) -> None:
        self.db = db
        self.llm = llm
        self.classification = ClassificationAgent(llm)
        self.root_cause = RootCauseAgent(llm)
        self.remediation = RemediationAgent(llm)
        self.executive_summary = ExecutiveSummaryAgent(llm)
```

Tests inject `FakeLLMClient`. See `.cursor/rules/andela-agentic-ai.mdc`.

## Anti-patterns

- Services importing from `fastapi.*` — they should be reusable by a CLI, scheduled job, or another service.
- Services holding a module-level `Session` — kills testability.
- Services swallowing exceptions to "be safe" — let them propagate or translate to domain exceptions.
- Services calling `genai.Client()` directly. Always go through the `LLMClient` protocol.

## Checklist

- [ ] Failing unit test added first
- [ ] Service is a class, depends only on `Session` (and `LLMClient` / clocks / ids if needed) via `__init__`
- [ ] No `HTTPException` inside the service — domain exceptions only
- [ ] Multi-statement writes wrapped in `with db.begin():` or explicit `db.commit()`
- [ ] No SQLAlchemy strings built via f-strings; bound parameters only
- [ ] Tests added for happy path AND zero/empty/edge cases

## See also

- `.cursor/skills/andela-tdd-loop/SKILL.md`
- `.cursor/skills/scaffold-api-endpoint/SKILL.md`
- `.cursor/rules/andela-fastapi-core.mdc`
- `.cursor/rules/andela-sql-safety.mdc`
- `.cursor/rules/andela-error-handling.mdc`
- `.cursor/rules/andela-agentic-ai.mdc` (when the service is part of triage)
