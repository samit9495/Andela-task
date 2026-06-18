# Andela Agentic Observability Platform — AGENTS.md

> Short overview for human readers and AI agents working in this repo.
> Rules and skills are defined under [`.cursor/`](.cursor/); read those first when working in a specific area.

## Project

The **Agentic Observability Platform** is an AI-powered SRE solution that ingests application logs, detects anomalies, correlates events into incidents, performs AI-assisted root cause analysis, recommends remediation steps, triggers alerts, and visualizes operational health. See [`Requirement_doc.md`](Requirement_doc.md) for the full specification.

## Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy 2.x (typed), Pydantic v2, SQLite, NumPy
- **AI**: google-genai SDK (Gemini 1.5 Flash) behind an `LLMClient` protocol; 4-agent triage (Classification → Root Cause → Remediation → Executive Summary); RAG over Markdown runbooks
- **Frontend**: React 18 + Vite + TypeScript (strict) + Recharts + TanStack Query
- **SDK**: `watchdog_client` (separate Python package, separate semver)
- **Quality**: Ruff, Black, Mypy
- **Tests**: pytest (+ AI evaluation suite), Vitest + React Testing Library
- **CI/CD**: GitHub Actions (Ruff → Black → Mypy → Pytest)
- **Deploy**: Docker + Docker Compose

## Repository layout (high-level)

```
Andela-task/
├── .cursor/              # rules, skills, agents, plan archive, mcp.json — read these first
│   └── plan/             # archived plan files from Cursor plan mode (workspace-tracked)
├── AGENTS.md             # this file
├── README.md             # public-facing setup, run, test instructions
├── Requirement_doc.md    # the spec
├── prompts.md            # complete history of LLM prompts (assessment requirement)
├── docker-compose.yml
├── tasks/                # todo, lessons, manual-test-scenarios
├── docs/                 # design notes, ADRs, AI evaluations, security reviews
├── deck/                 # presentation slides
├── backend/              # FastAPI backend
├── frontend/             # React UI
├── sdk/                  # watchdog_client SDK
├── tests/                # backend + AI evaluation tests
├── infra/                # Dockerfiles + GitHub Actions
├── data/runbooks/        # operational runbooks (RAG source)
└── scripts/synth/        # synthetic traffic generator
```

For the full anatomy with one-line responsibilities, read [`.cursor/rules/andela-project-map.mdc`](.cursor/rules/andela-project-map.mdc).

## How to work in this repo

1. **Always read `.cursor/rules/README.md` first.** It tells you which rules apply.
2. **TDD is non-negotiable.** Read [`.cursor/rules/andela-tdd-discipline.mdc`](.cursor/rules/andela-tdd-discipline.mdc) and follow [`.cursor/skills/andela-tdd-loop/SKILL.md`](.cursor/skills/andela-tdd-loop/SKILL.md).
3. **Every commit follows Conventional Commits** ([`.cursor/rules/andela-commit-hygiene.mdc`](.cursor/rules/andela-commit-hygiene.mdc)). One TDD step per commit.
4. **Track work** in [`tasks/todo.md`](tasks/todo.md). Capture lessons in [`tasks/lessons.md`](tasks/lessons.md).
5. **Every LLM prompt that ships gets logged to [`prompts.md`](prompts.md)** — this is an assessment requirement.

## AI agents available (for Cursor's Task tool)

These are personas in [`.cursor/agents/`](.cursor/agents/):

| Agent | Purpose | When to use |
|-------|---------|-------------|
| `andela-code-reviewer` | Full code review, including TDD audit, agentic correctness, and security | Before merging, after any non-trivial change |
| `andela-qa-automation` | Test coverage analysis + AI evaluation phase + manual test scenarios | When test coverage drops or before a release |
| `andela-security-reviewer` | Security-only review (secrets, injection, prompt injection, error leakage) | When sensitive areas are touched (ingestion, triage, RAG, alerts, config, auth) |

## Skills available

Skills are step-by-step recipes in [`.cursor/skills/`](.cursor/skills/):

- **TDD & quality**: `andela-tdd-loop`, `andela-testing`, `andela-code-quality`, `andela-errors`, `andela-fastapi-core`
- **Scaffolding**: `scaffold-api-endpoint`, `scaffold-service-layer`, `andela-frontend-react`
- **Domain (this project)**: `andela-agent-workflow`, `andela-rag-runbooks`, `andela-detection-strategy`, `andela-sdk-client`, `andela-synthetic-traffic`
- **Security & SQL**: `security-audit`, `sql-query-audit`
- **Decision-making**: `llm-council`

Trigger them with the keyword shortcuts defined in [`.cursor/rules/ai-shortcuts.mdc`](.cursor/rules/ai-shortcuts.mdc) (e.g., `TDD:`, `AUDIT:`, `SEC:`, `AGENT:`, `RAG:`, `DETECT:`, `EVAL:`, `COUNCIL:`).

## MCP servers (configured in `.cursor/mcp.json`)

| MCP | Purpose |
|-----|---------|
| Filesystem | Read/write within the project root |
| Git | Git operations on this repository |
| GitHub | Issues, PRs, releases via `${GITHUB_PERSONAL_ACCESS_TOKEN}` |
| Context7 | Up-to-date library documentation lookups |
| Docker | Container and Compose management |
| Browser | Inspect the running React dashboard |

All secrets come from environment variables documented in [`.env.example`](.env.example).

## Running the platform

See [`README.md`](README.md) for setup. Quick reference:

```bash
# install deps
pip install -e .
cd frontend && npm install

# run via Docker Compose
docker-compose up

# or run the backend directly
uvicorn backend.app.main:app --reload

# generate demo traffic
python -m scripts.synth.cli db_outage --duration 120 --seed 42

# tests
pytest -v -m "not ai_eval and not slow"
pytest -m ai_eval -v
cd frontend && npm run test -- --run
pytest sdk/tests -v
```
