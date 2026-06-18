# Security Review — main — 2026-06-18

Reviewer: `andela-security-reviewer` agent (driven by `.cursor/skills/security-audit/SKILL.md`)
Branch: `main` @ `87f2959`
Diff scope: post-remediation surface (`2c9f041..HEAD`) plus full-tree sweep for the 7 areas
Tools run: `Grep` patterns from the skill, `pip-audit` against the active virtualenv, manual reading of `main.py`, exception handlers, agents, sanitization helpers, middleware, MCP config, Dockerfile, GitHub Actions workflow, SDK transport, schemas.

## Summary

| Severity | Count |
| -------- | ----- |
| Critical | 0 |
| High     | 0 |
| Medium   | 4 |
| Low      | 2 |
| Info     | 3 |

The seven core areas (secrets, input validation, request size limits, error sanitization, SQL safety, prompt injection, PII / data leakage) come back **clean**. The remediation work (C1, W1–W6, W9) added explicit defenses — prompt-injection sanitization on signatures and runbooks, deterministic fallbacks for `LLMRateLimited` / `LLMAuthError`, an N+1 query fix, body-size middleware, ingestion isolation. All four agents now use `str.format` templates with `sanitize(...)` wrapping every untrusted field; the global exception handler returns `{"detail", "code"}` without stack traces; no f-string SQL; no checked-in secrets; MCP placeholders are all `${ENV_VAR}`.

The findings below are **hardening** items, not active vulnerabilities. Two should be addressed before exposing the API to the public internet (rate limiting + starlette CVEs); the others are defense-in-depth.

## Findings

### [MEDIUM] Gemini provider error string surfaces in domain-exception messages

**File**: `backend/app/triage/gemini_client.py:26-36`
**Issue**: `_translate_api_error` constructs every domain exception with `detail = str(exc)` where `exc` is a `google.genai.errors.APIError`. The `__str__` representation of those errors includes the provider's JSON response body (status, error message, sometimes project / quota identifiers, occasionally a fragment of the prompt). Today every agent wraps its call in `StructuredAgent._complete`, which catches `_LLM_FAILURES` and returns `None`, so this string is logged but not returned. However the global handler `handle_domain_error` in `backend/app/main.py:51-53` does `detail = str(exc) or code.replace("_", " ")` for any `LLMTimeout` / `LLMResponseInvalid` / `LLMRateLimited` / `LLMAuthError` that ever escapes an agent (e.g., direct `gemini_client.complete_structured(...)` usage from a future code path).
**Exploit / Impact**: If any future caller bypasses the agent fallback (or `StructuredAgent` is reused outside the four agents), the provider's raw error text — including internal project IDs, quota names, and possibly fragments of the prompt — would be returned to API clients via the HTTP body.
**Fix**: In `_translate_api_error`, replace `detail = str(exc)` with a sanitized, static-per-class string and log the full provider message at the call site:
```python
def _translate_api_error(exc: genai_errors.APIError) -> DomainError:
    code = getattr(exc, "code", None) or 0
    logger.warning("Gemini APIError code=%s message=%s", code, exc)
    if code in _AUTH_CODES:
        return LLMAuthError("LLM authentication failed")
    if code == 429:
        return LLMRateLimited("LLM rate limit exceeded")
    if isinstance(exc, genai_errors.ServerError):
        return LLMTimeout("LLM server error")
    return LLMResponseInvalid(f"LLM provider error (HTTP {code})")
```
**Rule**: `andela-security.mdc` § Error sanitization; `andela-error-handling.mdc` § Sanitize errors at the boundary.

### [MEDIUM] Production dependency `starlette 0.41.3` has 7 known CVEs

**File**: `pyproject.toml` (transitive via `fastapi`)
**Issue**: `pip-audit` reports seven advisories against `starlette 0.41.3`:
- `PYSEC-2026-161` (two)
- `CVE-2025-54121`, `CVE-2025-62727`, `CVE-2026-48818`, `CVE-2026-48817`, `CVE-2026-54283`, `CVE-2026-54282`

These cover multipart parsing DoS, StaticFiles path-handling issues, and other request-parsing flaws. Fix range: `starlette >= 1.3.1`, which requires bumping `fastapi`.
**Exploit / Impact**: Multiple low-effort DoS vectors against a publicly exposed `/api/v1/events` endpoint. The body-size middleware blunts the multipart-parsing CVEs but does not fully neutralize them.
**Fix**: Bump `fastapi` (and starlette by extension) to the latest compatible release in `pyproject.toml`, re-run the test suite, re-run `pip-audit`. Pin in `[tool.uv]` / `[project] dependencies` once green.
**Rule**: `andela-security.mdc` § Dependencies.

### [MEDIUM] CI dependency-audit job runs `pip-audit` without installing the project

**File**: `.github/workflows/ci.yml:86-104`
**Issue**: The `security` job in `.github/workflows/ci.yml` installs only `pip-audit` itself and then runs `pip-audit --progress-spinner=off`. Because the project is not installed in that job (no `pip install -e ".[dev]"`), `pip-audit` only sees its own dependencies — not `fastapi`, `starlette`, `google-genai`, `httpx`, etc. The 7 starlette CVEs above were therefore never going to fire this job.
**Exploit / Impact**: False sense of security — the CI gate that's supposed to surface dependency CVEs is effectively a no-op, which is how the starlette CVEs above slipped through.
**Fix**:
```yaml
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]" pip-audit

      - name: Audit dependencies
        run: pip-audit --progress-spinner=off
```
Optionally add `--ignore-vuln <id>` lines for any CVE with a documented compensating control, so the job stays green deliberately rather than accidentally.
**Rule**: `andela-security.mdc` § Dependencies (CI must enforce).

### [MEDIUM] No rate limit on `/api/v1/events` (cost / abuse risk for the LLM-backed pipeline)

**File**: `backend/app/api/routes/events.py`
**Issue**: `POST /api/v1/events` and `/events/batch` are publicly reachable, unauthenticated, and trigger the full triage pipeline (4 LLM calls per incident under live Gemini). A malicious client can DoS the service and / or drive unbounded Gemini token spend by replaying events at high volume. The W6 fix isolates ingestion from pipeline failures but does not throttle pipeline execution.
**Exploit / Impact**: With `USE_MOCK_AI=false`, an attacker who can reach `/api/v1/events` can drive arbitrary Gemini cost. With `USE_MOCK_AI=true` the impact reduces to plain DoS of the SQLite database.
**Fix**: Add `slowapi` (or equivalent) with a per-IP and / or per-API-key limit, e.g.:
- 60 events/min/IP for `POST /api/v1/events`
- 10 batches/min/IP for `POST /api/v1/events/batch`

Additionally enforce a global per-incident token budget in `TriageService` (already documented in `andela-agentic-ai.mdc` § Cost & rate guards but not implemented).
**Rule**: `andela-security.mdc` § Authentication & authorization (rate limit); `andela-agentic-ai.mdc` § Cost & rate guards.

### [LOW] Dev dependencies have known CVEs (pytest 8.3.4, black 24.10.0)

**File**: `pyproject.toml` `[project.optional-dependencies] dev`
**Issue**: `pip-audit` flags `pytest 8.3.4` (`CVE-2025-71176`) and `black 24.10.0` (`CVE-2026-32274`). Both are dev/test-only and not part of the runtime image, but they affect any developer / CI runner executing tests.
**Exploit / Impact**: Limited to local dev / CI machines; not exposed in production. Both fixes are minor version bumps (`pytest>=9.0.3`, `black>=26.3.1`).
**Fix**: Bump in `pyproject.toml`, re-run the suite, commit.
**Rule**: `andela-security.mdc` § Dependencies.

### [LOW] `EventCreate.metadata` field has no per-field size cap

**File**: `backend/app/schemas/event.py:22` (`metadata: dict[str, Any] | None = None`)
**Issue**: All other string fields have `max_length`, but `metadata` accepts an arbitrary dict bounded only by the global 1 MB body-size middleware. A single event could carry a metadata dict approaching the body cap.
**Exploit / Impact**: Defense-in-depth only — `BodySizeLimitMiddleware` already caps the request body. Without a per-field cap, the database row size could grow unexpectedly and surface as latency in downstream queries.
**Fix**: Add a Pydantic validator capping the serialized length, e.g.:
```python
@field_validator("metadata")
@classmethod
def _cap_metadata(cls, value: dict[str, Any] | None) -> dict[str, Any] | None:
    if value is None:
        return None
    if len(json.dumps(value)) > 8192:
        raise ValueError("metadata exceeds 8 KiB")
    return value
```
**Rule**: `andela-security.mdc` § Input validation (size limits per field, not just per request).

### [INFO] Dockerfile pins the Python base image by tag, not digest

**File**: `infra/Dockerfile.backend:4,13` (`FROM python:3.12-slim`)
**Issue**: For reproducible builds and supply-chain integrity, base images should be pinned by digest in production (`python:3.12-slim@sha256:...`). Tag-based pins float over time.
**Fix**: Resolve a known-good digest with `docker pull python:3.12-slim && docker inspect ...` and pin both `FROM` lines. Re-pin whenever the base image is intentionally updated.
**Rule**: `andela-security.mdc` § Docker (production hardening guidance).

### [INFO] `docs/llm_prompts.md` persists full prompts (including user content)

**File**: `backend/app/triage/prompt_log.py` → `docs/llm_prompts.md`
**Issue**: Every prompt — which includes sanitized but otherwise verbatim user-supplied event signatures, incident summaries, and runbook excerpts — is appended to `docs/llm_prompts.md`. The file is git-tracked and visible to anyone with repo access. This is **required** by the assessment (`andela-agentic-ai.mdc` § Mandatory prompt logging) but worth acknowledging as a data-residency consideration.
**Fix (if ever needed)**: For real production use, route the prompt log to a private store (S3 with bucket policy, dedicated DB table with RBAC) rather than a checked-in Markdown file. For the assessment scope, leave as-is and document the trade-off.
**Rule**: `andela-security.mdc` § PII-safe logging (intentional exception).

### [INFO] `RemediationOutput.references[*].title` is returned to API clients without sanitization

**File**: `backend/app/triage/agents/remediation_agent.py:40`
**Issue**: While `_runbook_block` correctly sanitizes runbook titles and content before injecting them into the prompt, the `RunbookReference(slug=r.slug, title=r.title)` constructor at line 40 uses the unsanitized title for the API response. Today `data/runbooks/*.md` is operator-controlled, so an attacker cannot inject content — but if runbooks were ever ingested from an untrusted source the title would surface to API consumers (and potentially to dashboards that render Markdown) without sanitization.
**Fix**: Apply `sanitize(r.title)` at line 40 as well, mirroring the prompt path. Cost: zero risk, zero perf impact.
**Rule**: `andela-rag.mdc` § Sanitize runbook content end-to-end (consistent with the prompt path).

## Threat-model notes (Phase 3)

| Question | Status |
| -------- | ------ |
| Can a malicious event `message` make an agent deviate from its category enum? | **No** — `_sanitize` strips control chars and injection markers; the structured-output schema with `IncidentCategory` enum rejects deviations; the fallback returns `UNKNOWN` with `confidence=0.0`. Verified by `tests/unit/test_prompt_sanitization.py`. |
| Does the agent output get returned verbatim to the API caller? | Yes, via `IncidentRead.summary` / `root_cause` / `recommended_actions`. Each field is Pydantic-validated and bounded (`max_length=2000`); the LLM cannot smuggle raw stack traces or secrets through schema validation. |
| Does the LLM have function-call / tool access? | **No.** `GenerateContentConfig` only sets `response_mime_type` and `response_schema`. |
| Can a caller cause unbounded LLM spend? | Partially. `max_tokens` is set per call (256–1024). Per-incident token budget is **not** enforced (Medium finding above). Rate limiting on `/api/v1/events` is **not** enforced (Medium finding above). |
| Is determinism preserved? | Yes. `temperature=0.0` is hard-coded in `StructuredAgent._complete` and passed through to `complete_structured`. |
| Are runtime Gemini prompts logged? | Yes. `PromptLog.record(...)` writes to both `llm_evaluations` and `docs/llm_prompts.md`. Verified during QA. |
| Does the SDK leak the API key on instantiation or in errors? | **No.** `WatchdogClient.__init__` puts the key in the `X-API-Key` header only; `WatchdogAPIError` carries the server's sanitized `code` + `detail` only; no logging in the SDK. |

## Bonus checks

| Check | Result |
| ----- | ------ |
| `.cursor/mcp.json` uses `${ENV_VAR}` placeholders only | **Pass** — `GITHUB_PERSONAL_ACCESS_TOKEN` and `CONTEXT7_API_KEY` are env-var references; no literal tokens. |
| `docker-compose.yml` does not bake secrets | **Pass** — `GEMINI_API_KEY: "${GEMINI_API_KEY:-}"`. |
| `Dockerfile.backend` runs as non-root | **Pass** — `useradd appuser`, `USER appuser`, `/data` owned by appuser. |
| `Dockerfile.backend` does not `COPY .env` | **Pass** — only `pyproject.toml`, `README.md`, `backend/`, `data/`. |
| `.env` is gitignored and not checked in | **Pass** — `.gitignore` excludes `.env`, only `.env.example` (placeholders) tracked. |
| GitHub Actions uses `${{ secrets.NAME }}` (never echo) | **Pass** — workflow does not reference any secrets explicitly today. |
| No `requests.get(user_input)` / SSRF surface | **Pass** — no outbound HTTP in `backend/` other than the in-memory dashboard / Slack / email channel stubs that accept no user-controlled URL. |

## Verdict

- [x] **Safe to merge** — no Critical or High findings; the four Medium items are hardening upgrades.
- [ ] Block — fix critical findings first
- [ ] Block — fix critical AND high findings first

### Recommended follow-ups (open as `tasks/todo.md` entries before exposing to the public internet)

1. **MEDIUM** — Bump `fastapi` / `starlette` past the 7 CVE range and re-pin.
2. **MEDIUM** — Fix the CI `security` job to install the project before running `pip-audit`.
3. **MEDIUM** — Sanitize `_translate_api_error` detail strings (`gemini_client.py`).
4. **MEDIUM** — Add per-IP rate limiting on `/api/v1/events` and a per-incident LLM-token budget.
5. **LOW** — Bump `pytest` and `black` dev dependencies past their CVE range.
6. **LOW** — Add a Pydantic validator capping `EventCreate.metadata` size (~8 KiB).
7. **INFO** — Pin Dockerfile base image by digest before production cut.
8. **INFO** — Sanitize `RunbookReference.title` for the response model (defense-in-depth).
