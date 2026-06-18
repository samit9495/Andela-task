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
