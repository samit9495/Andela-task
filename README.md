# Agentic Observability Platform

AI-powered SRE observability platform. It ingests application logs, detects
anomalies with deterministic statistics, correlates them into incidents, triages
each incident with a Gemini multi-agent pipeline (RAG over operational runbooks),
raises deduplicated alerts, scores platform risk, and visualizes everything on a
React dashboard.

The whole stack runs **offline with no secrets** — a deterministic heuristic AI
client (`USE_MOCK_AI=true`) stands in for Gemini so the demo, tests, and Docker
build need zero network access.

See [`MASTER_PLAN.md`](MASTER_PLAN.md) for the authoritative blueprint and
[`Intelligent Observability & Event Watchdog Doc.md`](Intelligent%20Observability%20&%20Event%20Watchdog%20Doc.md)
for the full specification.

## Architecture

```text
            ┌─────────────┐   POST /api/v1/events
  logs ───▶ │  Ingestion  │──────────────┐
            │ + Normalize │              ▼
            └─────────────┘        ┌───────────┐   z-score / EWMA / signature
                                   │ Detection │   frequency / severity drift
                                   └─────┬─────┘
                                         ▼
                                   ┌───────────┐
                                   │Correlation│──▶ Incident (+ risk score)
                                   └─────┬─────┘
                                         ▼
                 ┌───────────────────────────────────────────┐
                 │  Agentic triage (LLMClient protocol)        │
                 │  Classification → Root Cause → Remediation  │
                 │  → Executive Summary   (RAG over runbooks)  │
                 └───────────────────┬─────────────────────────┘
                                     ▼
                          Alerts (dashboard/webhook/slack/email sim)
                                     ▼
                            React dashboard + watchdog_client SDK
```

- **Thin routes → services → repositories/models** (FastAPI, SQLAlchemy 2.x, Pydantic v2).
- The LLM is always behind an `LLMClient` protocol; `MockAIClient` (offline) and
  `GeminiLLMClient` (live) are interchangeable. Tests never call the live API.
- Every runtime prompt is logged to `docs/llm_prompts.md` and the `llm_evaluations` table.

## Requirements

- Python 3.12+
- Node 20+ (for the dashboard)
- Docker + Docker Compose (optional, for the containerized stack)

## Quick start (Docker)

```bash
docker compose up --build
# Dashboard: http://localhost:5173
# API:       http://localhost:8000  (docs at /docs)
```

The frontend waits for the backend healthcheck, then serves the SPA and proxies
`/api` and `/health` to the backend. No `.env` is required (mock AI by default).

## Local development

### Backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

cp .env.example .env        # optional; defaults work for mock-AI mode

uvicorn backend.app.main:app --reload
curl http://localhost:8000/health
```

### Frontend

```bash
cd frontend
npm install
npm run dev                 # http://localhost:5173 (proxies /api to :8000)
```

### Generate demo traffic

```bash
# Scenarios: normal, db_outage, auth_failures, throttling,
#            memory_leak, dependency_failure, black_friday
python -m scripts.synth.cli db_outage --duration 120 --seed 42
python -m scripts.synth.cli black_friday --dry-run    # generate without sending
```

## API surface

| Method | Path | Purpose |
| --- | --- | --- |
| `GET`  | `/health` | Liveness probe |
| `GET`  | `/metrics` | Event/incident/alert counts + current risk score |
| `POST` | `/api/v1/events` | Ingest a single log event (triggers the pipeline) |
| `POST` | `/api/v1/events/batch` | Ingest up to 1000 events |
| `GET`  | `/api/v1/events` | List ingested events |
| `GET`  | `/api/v1/incidents` | List incidents |
| `GET`  | `/api/v1/incidents/{id}` | Incident detail incl. AI analysis |
| `GET`  | `/api/v1/alerts` | List raised alerts |
| `GET`  | `/api/v1/topology` | Service graph with incident-aware impact |
| `GET`  | `/api/v1/risk-score` | Current platform risk score |

## Python SDK

A standalone, separately-versioned client lives in [`sdk/`](sdk/):

```python
from watchdog_client import WatchdogClient, EventCreate

with WatchdogClient(base_url="http://localhost:8000") as client:
    client.create_event(EventCreate(service="payment-api", level="ERROR", message="db timeout"))
    incidents = client.get_incidents()
    risk = client.get_risk_score()
```

## Testing

```bash
# Fast inner loop (unit + integration + sdk), with coverage gate
pytest -m "not ai_eval and not slow" --cov=backend/app --cov-report=term-missing

# AI evaluation suite (deterministic, offline) + scorecard at artifacts/ai_evaluations.md
pytest -m ai_eval -v

# Frontend behavioral tests
cd frontend && npm run test -- --run
```

Coverage is held at **≥ 90%** in CI (currently ~99%).

## Quality gates

```bash
ruff check backend tests sdk scripts
black --check backend tests sdk scripts
mypy
```

CI ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) runs four jobs:
lint/type-check/test (with coverage floor), the AI evaluation suite, the frontend
build + Vitest, and a `pip-audit` dependency scan.

## Security

- All secrets come from the environment via `pydantic-settings`; none in source.
- Request body size limit (413) and a CORS allowlist are enforced as middleware.
- Pydantic validates every request boundary; errors are sanitized to `{detail, code}`.
- Untrusted log content is sanitized and delimited before entering any LLM prompt.

## Layout

```text
backend/app/      FastAPI app: core, db, models, schemas, repositories,
                  ingestion, detection, correlation, incidents, risk,
                  topology, alerts, triage (agents + RAG), pipeline, api
frontend/         React 18 + Vite + TS dashboard (Overview, Incidents,
                  AI Analysis, Topology)
sdk/              watchdog_client Python SDK (own semver)
scripts/synth/    synthetic traffic generator (7 scenarios)
tests/            unit + integration + ai_eval suites
data/runbooks/    RAG source (Markdown runbooks)
infra/            Dockerfiles + nginx config
deck/             presentation slides (Marp)
docs/             prompt audit logs and design notes
```

## License

MIT.
