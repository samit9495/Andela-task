# Tasks — todo.md

> Track every ticket / task here. See [`.cursor/rules/ai-workflow.mdc`](../.cursor/rules/ai-workflow.mdc) for the format.
>
> - Add a new entry under `## In Progress` when you start work.
> - Check off sub-tasks as you complete them.
> - Move the entry to `## Completed` with a one-line summary when done.
> - Capture surprises in [`lessons.md`](lessons.md).

## In Progress

<!-- Add new in-progress entries here. -->

## Completed

### 2026-06-18 — Phase 2: Detection + Correlation + Incidents + Risk
- [x] Detection constants in Settings (z-score/EWMA/signature/bucket/correlation) aliased to .env.example
- [x] Detector protocol + AnomalySignal; Z-Score, EWMA, Signature-Frequency detectors (pure NumPy) — TDD
- [x] Severity + IncidentStatus enums; Anomaly & Incident ORM models (1:N relationship) — TDD
- [x] AnomalyRepository (add_all, exists-dedup) + IncidentRepository (get, list, list_unresolved, find_open_for_service)
- [x] DetectionService: events -> per-minute bucketed series -> anomalies, naive-datetime coercion, window dedup — TDD
- [x] IncidentService (open/absorb, count-based severity, lifecycle) + CorrelationEngine (window-based grouping) — TDD
- [x] RiskScoreService (error/alert/incident penalties, clamp 0-100, Healthy/Warning/Critical bands) — TDD
- [x] Routes: GET /api/v1/incidents, GET /api/v1/incidents/{id} (404), GET /api/v1/risk-score — TDD
- **Status**: done
- **Summary**: 105 tests pass, 98% coverage; ruff/black/mypy green. Detectors are DB-agnostic and Liskov-substitutable. HTTP auto-trigger (ingest->detect->correlate) deferred to Phase 4 per plan; transformation proven at service level.

### 2026-06-18 — Phase 1: Ingestion & Normalization
- [x] Normalizer: strip numbers/UUID/timestamp/IP/hex -> stable signatures; standardize levels — TDD
- [x] LogLevel enum + Event ORM model (metadata->event_metadata to avoid reserved name) — TDD
- [x] EventRepository: add/add_all, list (service/level/since filters + pagination), count, count_by_level, count_distinct_services — TDD
- [x] Event schemas (EventCreate w/ tz-aware validator + extra=forbid, EventRead w/ metadata alias, BatchEventCreate min/max 1000, BatchEventResult) + MetricsResponse
- [x] IngestionService (normalize + persist single/batch, commit at boundary) — TDD
- [x] Routes: POST /api/v1/events, POST /api/v1/events/batch, GET /api/v1/events, GET /metrics — TDD
- [x] Wired routers into main; registered models in init_db + conftest
- **Status**: done
- **Summary**: 71 tests pass, 100% coverage; ruff/black/mypy green. CQRS-lite (writes via service, reads via repository). Signatures are placeholder templates (e.g. "Database timeout after <NUM> seconds").

### 2026-06-18 — Phase 0: Project Skeleton & Tooling
- [x] pyproject.toml (deps + ruff/black/mypy/pytest/coverage config)
- [x] .dockerignore (kept existing comprehensive .gitignore and .env.example)
- [x] Settings configuration loading (backend/app/core/config.py) — TDD
- [x] Domain exception hierarchy (backend/app/core/exceptions.py) — TDD
- [x] DB base, session, init_db (backend/app/db/) — TDD
- [x] Logging config (backend/app/core/logging.py)
- [x] App factory + lifespan + global exception handlers (backend/app/main.py) — TDD
- [x] GET /health endpoint + HealthResponse schema — TDD
- [x] tests/conftest.py fixtures (engine, db, client over in-memory SQLite)
- [x] Docker scaffolding (infra/Dockerfile.backend, .frontend, docker-compose.yml)
- [x] GitHub Actions CI (ruff→black→mypy→pytest)
- **Status**: done
- **Summary**: 21 tests pass, 100% coverage on backend/app; ruff/black/mypy all green. App boots and serves /health. No business logic (deferred to Phase 1+).

## Backlog

<!-- Pending ideas / nice-to-have items not yet scheduled. -->
