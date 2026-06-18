# Full Repository Review — Agentic Observability Platform

**Reviewer**: `andela-code-reviewer.md` checklist (all 13 sections)
**Scope**: Entire codebase (backend, SDK, scripts, frontend, infra, tests, docs) — not just recent changes
**Date**: 2026-06-18
**Commit at review**: `2c9f041` (72 commits total)

This review validates the implementation against `MASTER_PLAN.md`, the original
requirements (`Intelligent Observability & Event Watchdog Doc.md`), TDD discipline
in `git log`, architecture consistency, agentic-AI correctness, RAG, API
consistency, the SDK, and Docker/CI/CD. **No fixes were implemented.**

---

## Executive Summary

| | Count |
| --- | --- |
| **Critical** | 1 (REMEDIATED) |
| **Warnings** | 9 (7 REMEDIATED — W1, W2, W3, W4, W5, W6, W9; 2 deferred — W7, W8) |
| **Infos** | 8 |
| **Overall Readiness Score (post-remediation)** | **9 / 10** |
| **Recommendation** | **PASS** |

The codebase is well-structured, cleanly layered, and demonstrates **exemplary
TDD discipline** across the Python backend (clean `test:` → `feat:` alternation
over ~80 commits). Security hygiene is strong (no tracked secrets, Pydantic
validation everywhere, sanitized errors, body-size + CORS middleware). Tests are
comprehensive (246 passing fast suite, 98.75% backend coverage; 7 ai_eval cases;
17 SDK cases; 3 frontend cases). The Critical and the seven targeted Warnings
(C1, W1–W6, W9) were remediated TDD-style (RED test → GREEN implementation, one
finding per pair of commits). The two deferred items (W7 git history hygiene,
W8 SDK 5xx retry-with-backoff) are explicitly out of scope per the remediation
plan and do not block the assessment.

---

## Checklist coverage (andela-code-reviewer.md)

| Section | Result |
| --- | --- |
| 1. TDD discipline (git log) | Strong; 2 hygiene deviations (W7) |
| 2. Craftsmanship | Strong; small files, intent-revealing names, named constants |
| 3. FastAPI layering | Mostly thin; minor route-level data access (I1) |
| 4. SQL safety | ORM throughout, parameterized; one N+1 (W2) |
| 5. Error handling | Good; LLM live-mode gap (C1) |
| 6. Agentic AI | Protocol-bound, structured, logged; sanitize gap (W1) |
| 7. RAG | top_k + floor + deterministic tie-break; prod embedder (I2) |
| 8. Detection engine | Deterministic, settings-driven, edge-cased |
| 9. Tests | Boundary-mocked, no live LLM, no snapshots |
| 10. SDK | Decoupled, typed; missing `get_health` (W4), retry policy (W8) |
| 11. Code quality / edge cases | Good; risk windowing (W3) |
| 12. API response consistency | All 9 endpoints present; batch status (I) |
| 13. Security | Strong across the board |

---

## Remediation status (this branch)

| Finding | Status | TDD commits |
| --- | --- | --- |
| C1 | **FIXED** | `test(triage): translate Gemini provider errors…` → `fix(triage): translate Gemini provider errors…` |
| W1 | **FIXED** | `test(triage): event signatures and runbook excerpts…` → `fix(triage): sanitize event signatures and runbook excerpts…` |
| W2 | **FIXED** | `test(repo): incident list queries must not N+1…` → `fix(repo): eager-load incident anomalies…` |
| W3 | **FIXED** | `test(risk): error rate must be windowed…` → `fix(risk): scope error-rate to a configurable rolling window` |
| W4 | **FIXED** | `test(sdk): get_health() returns typed HealthStatus…` → `feat(sdk): add get_health() returning typed HealthStatus` |
| W5 | **FIXED** | `test(ai_eval): summary-quality rubric…` → `feat(ai_eval): score executive-summary quality in the report` |
| W6 | **FIXED** | `test(events): ingestion must not 5xx when the pipeline raises` → `fix(events): isolate pipeline errors from the ingestion response` |
| W7 | Deferred — cannot retroactively split pushed commits | — |
| W8 | Deferred — out of scope for this branch | — |
| W9 | **FIXED** | `test(incidents): cover PATCH /incidents/{id}…` → `feat(incidents): expose PATCH /incidents/{id}…` |
| I1–I8 | Informational; not addressed in this branch | — |

Post-remediation gate snapshot: ruff/black/mypy clean; 246 fast tests pass at
98.75% backend coverage (≥90% gate); 7 ai_eval pass (incl. new summary-quality
metric); 17 SDK tests pass (incl. new `get_health` happy/timeout); 3 frontend
tests pass.

---

## Critical Issues

### C1 — Live Gemini provider errors are not translated to domain exceptions
**Status: FIXED.** `GeminiLLMClient.complete_structured` now catches
`google.genai.errors.APIError` and maps by HTTP status (429 → `LLMRateLimited`,
401/403 → new `LLMAuthError` raised immediately without retry, other 4xx →
`LLMResponseInvalid`, 5xx → `LLMTimeout`). `StructuredAgent._complete` now
includes `LLMRateLimited` and `LLMAuthError` in `_LLM_FAILURES`, so a single
provider error never crashes a triage request. `main.py` maps both new domain
exceptions to sanitized JSON responses.

- **Severity**: Critical
- **File**: `backend/app/triage/gemini_client.py` (lines 48–58)
- **Issue**: `complete_structured` only catches `TimeoutError`, `ValidationError`,
  and `ValueError`. Real `google-genai` failures — rate limit (429), auth (401),
  and generic API/transport errors — are **not** caught and are **not** mapped to
  `LLMRateLimited` / `LLMTimeout` / `LLMResponseInvalid`. `StructuredAgent._complete`
  (`base_agent.py` line 13) only catches `(LLMTimeout, LLMResponseInvalid,
  LLMRateLimited)`, so an untranslated provider error propagates up through
  `TriageService.triage` → `PipelineService.process_service` → `POST /api/v1/events`,
  producing a 500 **after the event was already persisted**. This violates the
  mandatory LLM-failure-path rule (`andela-error-handling.mdc`: timeout, rate
  limit, auth, malformed JSON each need a defined behavior) and the "triage must
  never crash the whole request" guarantee.
- **Impact**: Live-mode only (the offline `MockAIClient` default, demo, and CI are
  unaffected — which is why all tests pass). But the headline feature is the
  agentic pipeline, and its production client is not resilient.
- **Recommended Fix**: In `GeminiLLMClient`, catch the google-genai error types
  (e.g. `google.genai.errors.APIError` / `ClientError` / `ServerError`) and map
  HTTP 429 → `LLMRateLimited`, 401/403 → a non-retryable auth domain error
  (raise immediately, do not retry), timeouts → `LLMTimeout`, everything else →
  `LLMResponseInvalid`. Add `LLMRateLimited` to the retry-with-backoff path. Cover
  with a unit test per branch using a fake client that raises each provider error.

---

## Warnings

### W1 — Prompt-injection sanitization is incomplete (only some fields sanitized) — FIXED
- **Severity**: Warning
- **Files**: `backend/app/triage/base_agent.py` (`format_top_events`, lines 67–72);
  `backend/app/triage/agents/classification_agent.py` (line 19);
  `backend/app/triage/agents/root_cause_agent.py`;
  `backend/app/triage/agents/remediation_agent.py` (`_runbook_block`, lines 43–49)
- **Issue**: Only `incident_summary` and `root_cause` pass through `sanitize()`.
  The `top_events_block` (built from event-derived **signatures**) and the runbook
  excerpts are injected into prompts **without** sanitization. A crafted log message
  can produce a signature containing injection markers (e.g. `### system`,
  `<<<END>>>`) that reach the Classification/Root-Cause prompts unsanitized via
  `top_events_block`. The normalizer (`normalizer.py`) only masks numbers/UUIDs/IPs,
  not injection markers, so the marker survives into the signature.
- **Recommended Fix**: Apply `sanitize()` to each signature inside
  `format_top_events`, and to runbook title/content inside `_runbook_block`. Add a
  unit test feeding a signature with `<<<END>>>`/`### system` and asserting the
  rendered prompt contains `[REDACTED]`.

### W2 — N+1 query when listing incidents (anomalies lazily loaded) — FIXED
- **Severity**: Warning
- **Files**: `backend/app/repositories/incident_repository.py` (`list`, lines 44–56;
  `list_unresolved`, lines 28–30); `backend/app/schemas/incident.py` (line 49,
  `anomalies: list[AnomalyRead]`)
- **Issue**: `IncidentRead` serializes `anomalies`, but neither `list` nor
  `list_unresolved` eager-loads them. `GET /api/v1/incidents` therefore issues one
  query for the incidents plus one per incident for its anomalies (N+1). The
  reviewer checklist (§4) explicitly calls for `selectinload(Incident.anomalies)`
  on list endpoints.
- **Recommended Fix**: Add `.options(selectinload(Incident.anomalies))` to the list
  queries. Optionally assert the query count in a test.

### W3 — Risk score error-rate uses lifetime totals, not the documented window — FIXED
- **Severity**: Warning
- **File**: `backend/app/risk/risk_score_service.py` (lines 47–53)
- **Issue**: `error_rate_pct` is computed from `event_repo.count()` and
  `count_by_level()` over **all events ever ingested**. `MASTER_PLAN.md` §26.3 says
  `error_rate_pct = % of window events at ERROR/CRITICAL`. With lifetime totals,
  accumulated INFO events dilute the ratio so a recent error spike barely moves the
  score — the risk score lags reality.
- **Recommended Fix**: Restrict the error-rate calculation to a recent window
  (e.g. the correlation/detection window) via a `since` filter on the event counts.
  Add a test asserting the score reacts to a recent spike while old INFO volume is
  excluded.

### W4 — SDK is missing the required `get_health()` method — FIXED
- **Severity**: Warning
- **File**: `sdk/watchdog_client/client.py` (public API, lines 49–99)
- **Issue**: Requirements §7 and `andela-sdk.mdc` list six public functions:
  `create_event`, `create_batch`, `get_incidents`, `get_alerts`, `get_risk_score`,
  **`get_health`**. The SDK implements five; `get_health()` is absent. `/health`
  exists on the backend.
- **Recommended Fix**: Add `get_health()` (typed return model) test-first against a
  respx-mocked `/health`, and bump the SDK minor version + CHANGELOG (new endpoint).

### W5 — AI-evaluation suite is missing the "summary quality" metric — FIXED
- **Severity**: Warning
- **Files**: `tests/ai_eval/` (`test_classification_accuracy.py`,
  `test_root_cause_accuracy.py`, `test_remediation_quality.py`, `report.py`)
- **Issue**: Requirements §10 mandates four AI-eval metrics: classification
  accuracy, root-cause accuracy, remediation quality, **and summary quality**. The
  Executive Summary Agent has unit tests but no evaluation-suite metric, and the
  scorecard (`report.py`) does not score summaries.
- **Recommended Fix**: Add `test_summary_quality.py` with a rubric (e.g. summary
  references the category/subsystem and is within a sentence range) and a
  `summary_quality` column in `report.py`/`artifacts/ai_evaluations.md`.

### W6 — Full pipeline (incl. LLM triage) runs synchronously inside POST /events — FIXED (durability decoupled)
- **Severity**: Warning
- **Files**: `backend/app/api/routes/events.py` (`_run_pipeline`, lines 27–58);
  `backend/app/pipeline/pipeline_service.py`
- **Issue**: Each `POST /events` and `/events/batch` runs detection → correlation →
  triage (up to four LLM calls) → alerting **in the request path**. Two concerns:
  (1) under live Gemini this adds large, blocking latency to ingestion; (2) the
  event is persisted before `_run_pipeline`, so a pipeline exception returns 500 to
  a client whose data was actually accepted — encouraging retries / duplicate
  ingestion. Ingestion durability should not depend on triage success.
- **Recommended Fix**: Decouple — run the pipeline in a background task / queue, or
  at minimum wrap `_run_pipeline` so pipeline failures are logged and swallowed
  (ingestion still returns 201). Document the chosen async strategy.

### W7 — Two commits bundle tests with implementation (TDD hygiene)
- **Severity**: Warning
- **Commits**: `e9566c8` "feat: enforce request body size limit and CORS allowlist"
  (adds `test_security_middleware.py` + `test_cors.py` **and** the middleware in one
  commit); `98f6536` "feat(frontend): React + Vite dashboard…" (adds `*.test.tsx`
  **and** the components in one commit)
- **Issue**: `andela-tdd-discipline.mdc` and `andela-commit-hygiene.mdc` require the
  failing `test:` commit to precede the `feat:` commit. These two bundle both. The
  rest of the history (≈60 commits) is exemplary, so this is a localized deviation,
  not a pattern.
- **Recommended Fix**: For future work, commit the RED test first. (Not worth
  rewriting pushed history; note it and keep the discipline going forward.)

### W8 — SDK retry policy does not match the documented contract
- **Severity**: Warning
- **File**: `sdk/watchdog_client/client.py` (`_get`, lines 117–125; `_post`, 127–133)
- **Issue**: `andela-sdk.mdc` specifies "retries on connection errors **and 5xx**
  responses, with **exponential backoff**." The implementation retries GET only on
  transport/timeout exceptions (not on 5xx) and uses an immediate loop with no
  backoff. POST is intentionally not retried (reasonable for non-idempotency).
- **Recommended Fix**: Either implement 5xx retry with exponential backoff for
  idempotent GETs, or update the SDK rule/README to document the deliberately
  narrower policy. Keep POST non-retried.

### W9 — No incident status-transition endpoint (lifecycle not exposed) — FIXED
- **Severity**: Warning
- **Files**: `backend/app/api/routes/incidents.py` (read-only);
  `backend/app/incidents/incident_service.py` (`update_status`, lines 69–77, unused
  by any route)
- **Issue**: Requirements Component 7 describes an incident lifecycle
  (open → investigating → resolved). `IncidentService.update_status` exists and is
  tested but is not wired to any API route, so incidents cannot be transitioned/
  resolved via the API or dashboard. This also means `resolved_at` is never set in
  practice, and `list_unresolved` (used by risk score) grows unbounded.
- **Recommended Fix**: Expose a `PATCH /api/v1/incidents/{id}` (or
  `POST .../{id}/status`) endpoint returning 200, validated by an enum body, mapping
  to `update_status`. Add an integration test (incl. 404).

---

## Info

### I1 — Minor thin-route deviations (routes performing data access)
- **Files**: `backend/app/api/routes/topology.py` (`_impacted_services` builds
  `IncidentRepository` and queries in the route, lines 33–40);
  `backend/app/api/routes/metrics.py` (instantiates three repositories + service
  directly, lines 18–25); `backend/app/api/routes/alerts.py` (injects a repository
  rather than a service)
- **Issue**: Checklist §3 prefers routes to call a service. These embed data-access
  composition in the route layer.
- **Recommended Fix**: Extract a `TopologyService` / `MetricsService` to own the
  composition; routes stay parse → call → return.

### I2 — RAG production embedder is the hashing (offline) embedder
- **File**: `backend/app/rag/retriever.py` (`build_runbook_retriever`, lines 50–59)
- **Issue**: `andela-rag` envisions `HashEmbedder` for tests and a real embedder
  (e.g. Gemini `text-embedding-004`) in prod. Both paths use `HashingEmbedder`. The
  `Embedder` protocol makes this swappable, so it is a deliberate scope choice.
- **Recommended Fix**: Document explicitly as a scope decision, or add a
  `GeminiEmbedder` behind the protocol for live mode.

### I3 — Triage prompt hardcodes event level as "ERROR"
- **File**: `backend/app/triage/triage_service.py` (`_top_events`, lines 104–108)
- **Issue**: Every anomaly is reported to the agents with `level="ERROR"`,
  discarding real severity; weakens the signal available to classification.
- **Recommended Fix**: Carry the dominant level from the anomaly/events into the
  tuple.

### I4 — `normalize_level` flattens DEBUG/TRACE to INFO
- **File**: `backend/app/ingestion/normalizer.py` (lines 40–41)
- **Issue**: DEBUG and TRACE map to `INFO`, losing granularity. Documented behavior,
  but may surprise consumers.
- **Recommended Fix**: Confirm intended; otherwise add a `DEBUG` level.

### I5 — SDK models use `str` instead of `Literal`; EventCreate lacks tz-aware check
- **File**: `sdk/watchdog_client/models.py` (lines 15–26, 69–84)
- **Issue**: `andela-sdk.mdc` suggests `Literal` enums for fixed sets
  (level/severity/status). SDK uses plain `str`. Also `EventCreate.timestamp` is not
  validated as timezone-aware client-side, while the backend rejects naive datetimes
  (422) — the failure surfaces only at the server.
- **Recommended Fix**: Use `Literal[...]` for fixed sets and validate tz-aware
  timestamps in the SDK to fail fast.

### I6 — PromptLog commits the DB and appends markdown on every agent call
- **File**: `backend/app/triage/prompt_log.py` (`record`, lines 51–81)
- **Issue**: Each agent call performs its own `commit()` + file append inside the
  request path (4 commits + 4 file appends per incident triage). Fine for the
  assessment's auditability requirement; a throughput concern at scale.
- **Recommended Fix**: Batch the DB writes / buffer the markdown if performance
  matters later.

### I7 — Batch endpoint returns 201, checklist suggests 202 (accepted)
- **File**: `backend/app/api/routes/events.py` (lines 46–59)
- **Issue**: Checklist §12 suggests `202` for batch accept. The batch is processed
  synchronously and returns `201`. Defensible given synchronous processing.
- **Recommended Fix**: Use `202` if/when batch ingestion becomes asynchronous.

### I8 — `print()` in the synthetic CLI
- **File**: `scripts/synth/cli.py` (line 77)
- **Issue**: A `print` is used for CLI user output. Acceptable for a CLI tool (not
  debug output), noted for completeness.
- **Recommended Fix**: None required; could move to `logging` for consistency.

---

## Validation against MASTER_PLAN & Requirements

### Requirements coverage (Doc §8 API)
All nine required endpoints are implemented: `/health`, `/metrics`,
`POST /events`, `GET /events`, `/incidents`, `/incidents/{id}`, `/alerts`,
`/risk-score`, `/topology`. ✅

### Components (Doc §5)
| Component | Status |
| --- | --- |
| 1 Log Ingestion | ✅ single + batch, validated, normalized |
| 2 Event Normalization | ✅ stable signatures + level standardization |
| 3 Synthetic Traffic | ✅ 7 deterministic scenarios + CLI |
| 4 Detection Engine | ✅ z-score, EWMA, signature-frequency |
| 5 Correlation Engine | ✅ window-based grouping/absorption |
| 6 Topology Engine | ✅ blast radius + root service |
| 7 Incident Management | ⚠️ lifecycle method exists but no status route (W9) |
| 8 Agentic Triage | ✅ 4 agents; ⚠️ live error path (C1), sanitize gap (W1) |
| 9 Runbook RAG | ✅ loader/embedder/retriever/citations |
| 10 AI Incident Summary | ✅ executive summary agent |
| 11 Alert Engine | ✅ 4 channels, dedup, rate-limit, sanitized payload |
| 12 Risk Score | ⚠️ implemented; windowing deviation (W3) |
| 13 Dashboard | ✅ Overview/Incidents/AI Analysis/Topology |

### Testing (Doc §10)
Unit (detection/correlation/risk) ✅, integration (APIs/DB) ✅, AI-eval
classification/root-cause/remediation ✅, **summary quality ❌ (W5)**. Target
coverage 90%+ ✅ (≈99% backend, gated in CI).

### Security (Doc §9)
Env-var secrets ✅, no hardcoded keys ✅ (`.env` untracked + gitignored, `mcp.json`
uses `${ENV}` placeholders), Pydantic validation on every boundary ✅, request
size limits ✅ (4000-char message, 1000-event batch, body-size middleware), error
sanitization ✅.

### CI/CD (Doc §11)
Ruff → Black → Mypy → Pytest all present and fail the build; plus AI-eval,
frontend, and pip-audit jobs and a 90% coverage floor. ✅

### Docker (Doc §12)
Backend + frontend containers, SQLite volume, `docker compose up/down`; healthchecks
and `service_healthy` dependency. Compose config validates; frontend prod build
verified. (Image build not run here — Docker daemon unavailable in the review
environment.) ✅

### TDD discipline (git log)
~60 backend commits show clean `test:` → `feat:`/`refactor:` alternation,
Conventional Commits throughout, no `wip`/`final v2` messages. Two bundling
deviations (W7). Overall: strong. ✅

---

## Strengths

- Disciplined, readable TDD history that an assessor can follow commit-by-commit.
- Clean layering: thin routes → services → repositories; ORM-only data access.
- LLM strictly behind the `LLMClient` protocol; structured Pydantic outputs;
  per-call prompt logging to `llm_evaluations` **and** `docs/llm_prompts.md`.
- Deterministic, offline-capable detection, RAG, and AI-eval (no network in tests).
- Strong security posture and consistent `{detail, code}` error contract.
- Small, single-responsibility files (largest backend module 130 lines).

---

## Recommendation

**PASS WITH CONDITIONS — Readiness 8/10.**

The platform is feature-complete against the requirements and demonstrates the
engineering discipline the assessment rewards. Before final submission, address:

1. **C1** — translate live Gemini provider errors to domain exceptions (resilience
   of the headline feature).
2. **W4** — add the required SDK `get_health()`.
3. **W5** — add the required "summary quality" AI-evaluation metric.

W1 (sanitization completeness), W2 (N+1), W3 (risk windowing), W6 (synchronous
pipeline), and W9 (incident lifecycle endpoint) are recommended next. The Infos are
polish. None of the findings require structural rework.
