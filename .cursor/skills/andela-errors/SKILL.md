---
name: andela-errors
description: Short companion for FastAPI error handling — domain exceptions, exception handlers, response shape, LLM failure paths. Use when writing try/except, raising HTTPException, or returning error payloads.
---

# Andela Errors (skill)

Companion to `.cursor/rules/andela-error-handling.mdc`.

## Layered responsibility

| Layer | Action |
|-------|--------|
| Repository | Lets `sqlalchemy.exc.*` bubble. Does not translate. |
| External adapter (LLM, webhook) | Translates network errors to adapter exceptions (`LLMTimeout`, `LLMResponseInvalid`). |
| Service | Translates DB / adapter conditions to project exceptions (`IncidentNotFound`, `EventValidationError`, `TriageFailed`). |
| Route | Does nothing — the handler maps. |
| `main.py` | `@app.exception_handler(DomainError)` returns JSON. |

## Domain exception template

```python
# backend/app/core/exceptions.py
class DomainError(Exception): ...

class IncidentNotFound(DomainError):
    def __init__(self, incident_id: int):
        super().__init__(f"incident {incident_id} not found")
        self.incident_id = incident_id

class TriageFailed(DomainError):
    """Agentic triage could not produce a structured output."""

class LLMTimeout(DomainError): ...
class LLMResponseInvalid(DomainError): ...
```

## Handler template

```python
@app.exception_handler(IncidentNotFound)
async def handle_not_found(_, exc: IncidentNotFound):
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc), "code": "incident_not_found"},
    )


@app.exception_handler(TriageFailed)
async def handle_triage_failed(_, exc: TriageFailed):
    return JSONResponse(
        status_code=503,
        content={"detail": "Triage temporarily unavailable", "code": "triage_failed"},
    )
```

## Response shape

```json
{ "detail": "human message", "code": "machine_code" }
```

## LLM failure cheat-sheet

| Failure | Strategy |
|---------|----------|
| Timeout | Retry once → raise `LLMTimeout` → Executive Summary Agent falls back to deterministic summary, `confidence=0.0` |
| Rate limit | Backoff + retry per Google AI guidance → raise `LLMRateLimited` after max retries |
| Malformed JSON / fails Pydantic | Retry with "JSON only" follow-up → raise `LLMResponseInvalid` |
| Auth (401) | No retry; raise immediately, alert ops |

The whole triage pipeline must **never** crash because of a single agent failure.

## Don'ts

- No bare `except Exception` in services or routes.
- No `print` for errors. Use `logger.exception(...)`.
- No silent swallow. Re-raise or translate.
- Never leak stack traces or LLM raw responses in error bodies (see `andela-security.mdc`).

## See also

- Rule: `.cursor/rules/andela-error-handling.mdc`
- Rule: `.cursor/rules/andela-api-routes.mdc` (HTTP status semantics)
- Rule: `.cursor/rules/andela-agentic-ai.mdc` (agent fallbacks)
- Rule: `.cursor/rules/andela-security.mdc` (sanitization)
