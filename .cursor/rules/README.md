# Andela Cursor Rules

Project-specific rules for the **Agentic Observability Platform** (the Andela assessment).

## Related project AI assets

| Location | Purpose |
|----------|---------|
| [`../skills/`](../skills/) | Task-focused **skills** (`SKILL.md` per folder) aligned with these rules |
| [`../agents/`](../agents/) | **Agent personas** (code reviewer, QA automation, security reviewer) |
| [`../mcp.json`](../mcp.json) | MCP server configuration (Filesystem, Git, GitHub, Context7, Docker, Browser) |
| [`../../AGENTS.md`](../../AGENTS.md) | Project overview, stack, agent roles |
| [`../../tasks/lessons.md`](../../tasks/lessons.md) | Team **lessons learned** (promote stable items into rules/skills) |
| [`../../prompts.md`](../../prompts.md) | Required prompt history (Req. doc Section 15) |

## Always-Apply Rules (read first, top-to-bottom)

### Craftsmanship — THE values the assessor reads code against

| Rule | Purpose |
|------|---------|
| **andela-tdd-discipline** | Uncle Bob's Three Laws of TDD. The primary rule. Failing test before any production code. |
| **andela-craftsmanship** | SOLID, Clean Code, Simple Design, YAGNI/DRY/KISS. |
| **andela-commit-hygiene** | Conventional Commits; one TDD step per commit; the git log tells the story. |

### Tech conventions

| Rule | Purpose |
|------|---------|
| **andela-fastapi-core** | Stack (FastAPI + SQLAlchemy 2 + Pydantic v2 + SQLite + NumPy + Gemini/google-genai); layered architecture (routes → services → repositories → models) |
| **andela-error-handling** | Domain exceptions, FastAPI exception handlers, structured error payloads, LLM failure paths |
| **andela-code-quality** | Concrete smell catalog and edge-case guards (companion to craftsmanship) |
| **andela-testing** | pytest + Vitest, TDD-first, ≥ 90% coverage on changed modules, **AI evaluation tests**, characterization tests before legacy refactor |

### Domain conventions (new for this project)

| Rule | Purpose |
|------|---------|
| **andela-agentic-ai** | LLMClient protocol, structured outputs, the 4-agent triage workflow, mandatory `prompts.md` logging, determinism, cost guards |
| **andela-detection-engine** | Z-Score / EWMA / signature frequency / severity drift; NumPy; deterministic; no magic thresholds |
| **andela-rag** | Runbook loader → embedder → retriever → injection; mandatory citations; deterministic ordering |
| **andela-sdk** | `watchdog_client` SDK design: typed, semver, no business logic, decoupled from backend |
| **andela-security** | Env secrets, Pydantic validation, request limits, error sanitization, PII-safe logging, **prompt-injection defenses** |

### AI behavior

| Rule | Purpose |
|------|---------|
| **ai-workflow** | Planning (incl. plan archive at `.cursor/plan/`), task tracking via `tasks/todo.md`, subagent strategy, lessons |
| **ai-standards** | Response style, verification before done, elegance, core principles |
| **ai-shortcuts** | Keyword triggers (TDD, RED, GREEN, REFACTOR, AUDIT, TESTS, BUG, SEC, AGENT, RAG, DETECT, EVAL, ULTRA, DELPHI, COUNCIL, etc.) |

## File-Scoped Rules (apply when matching files are edited)

| Rule | Globs | Purpose |
|------|-------|---------|
| **andela-api-routes** | `backend/app/api/**/*.py`, `backend/app/main.py` | FastAPI router patterns, response_model, HTTPException |
| **andela-sql-safety** | `backend/app/repositories/**`, `backend/app/db/**`, `backend/app/models/**`, `backend/app/**/*service*.py` | Parameterized SQL only, ORM by default |
| **andela-frontend-react** | `frontend/**/*.{ts,tsx,...}` | React 18 + Vite + Recharts + TanStack Query for the 5 dashboard pages; Browser MCP for inspection |
| **andela-project-map** | `backend/**`, `frontend/**`, `sdk/**`, `tests/**`, `scripts/**`, `infra/**` | Where things live |
| **andela-detection-engine** | `backend/app/detection/**`, `tests/unit/test_detection_*.py` | Detection strategy patterns |
| **andela-rag** | `backend/app/rag/**`, `data/runbooks/**`, `tests/unit/test_rag_*.py` | RAG pipeline patterns |
| **andela-sdk** | `sdk/**` | SDK design rules |

## Reading order

If you only read one section before writing code:

1. **`andela-tdd-discipline`** — the loop.
2. **`andela-commit-hygiene`** — how the loop becomes commits.
3. **`andela-craftsmanship`** — the principles that make the code clean.
4. **`andela-security`** — non-negotiable baseline for every change.
5. Then the tech rule that matches what you are editing (`andela-agentic-ai` for the triage area, `andela-detection-engine` for detectors, `andela-rag` for runbooks, etc.).

## Cross-references

- TDD ↔ commit hygiene ↔ testing form a triangle. Each one references the other two.
- Craftsmanship is the why; code-quality is the concrete how.
- Error handling defers to FastAPI core for layering; FastAPI core defers to error handling for exception strategy.
- Security threads through every domain rule — see the "See also" section in each.
- Project map is a skeleton — keep it current as files are added.
