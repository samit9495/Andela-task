# Agentic Observability Platform

AI-powered SRE observability platform: ingest logs, detect anomalies with
deterministic statistics, correlate them into incidents, triage with a Gemini
multi-agent pipeline (RAG over runbooks), raise alerts, score risk, and
visualize health on a dashboard.

See [`MASTER_PLAN.md`](MASTER_PLAN.md) for the authoritative blueprint and
[`Intelligent Observability & Event Watchdog Doc.md`](Intelligent%20Observability%20&%20Event%20Watchdog%20Doc.md)
for the full specification.

## Status

Phase 0 (Project Skeleton & Tooling) complete: FastAPI app boots, configuration
loads from the environment, the database initializes on startup, and
`GET /health` is live. No business logic yet.

## Requirements

- Python 3.12+
- (Later phases) Node 20+ for the dashboard, Docker for deployment

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Copy env template and fill in values (optional for mock-AI mode)
cp .env.example .env
```

## Run

```bash
uvicorn backend.app.main:app --reload
# Health check
curl http://localhost:8000/health
```

## Test

```bash
# Fast suite with coverage
pytest -m "not ai_eval and not slow" --cov=backend/app --cov-report=term-missing

# Everything
pytest
```

## Quality gates

```bash
ruff check backend tests
black --check backend tests
mypy
```

## Docker

```bash
docker-compose up      # builds and runs the backend (frontend enabled in Phase 4)
docker-compose down
```

## Layout

```text
backend/app/      FastAPI app (core, db, api, and domain engines added per phase)
tests/            unit + integration (AI eval + sdk suites added later)
infra/            Dockerfiles
data/runbooks/    RAG source (added in Phase 3)
docs/             prompt audit logs and design notes
```
