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

### 2026-06-18 — Repository review remediation (C1, W1-W6, W9)
- [x] C1: Translate google.genai APIError -> domain exceptions (LLMRateLimited / new LLMAuthError / LLMResponseInvalid / LLMTimeout); broaden _LLM_FAILURES; auth raises without retry; new handler mappings in main.py — TDD
- [x] W1: Sanitize event signatures in format_top_events and runbook title/excerpt in RemediationAgent._runbook_block — TDD with FakeLLMClient prompt capture
- [x] W2: selectinload(Incident.anomalies) on IncidentRepository.list and list_unresolved with .unique(); query-count test via after_cursor_execute listener — TDD
- [x] W3: Add EventRepository.count/count_by_level since= filter; new WATCHDOG_RISK_ERROR_RATE_WINDOW_SECONDS (default 900); clock-injectable RiskScoreService.calculate(now=...); risk integration test now uses wall-clock now — TDD
- [x] W4: SDK get_health() returning typed HealthStatus; export the model; bump to 0.2.0 + CHANGELOG entry; respx happy + timeout — TDD
- [x] W5: expected_summary_keywords on all 5 ai_eval fixtures; new @ai_eval test_summary_quality; report.py + evaluation-report assertions extended with summary_quality metric; MockAIClient now honors explicit Category: line so chained-agent prompts stay consistent — TDD
- [x] W6: Wrap _run_pipeline in try/except + logger.exception, so POST /events and /events/batch always return 201 after persistence even when the pipeline raises — TDD
- [x] W9: PATCH /api/v1/incidents/{id} + IncidentStatusUpdate schema (extra="forbid"), delegating to IncidentService.update_status — TDD with RESOLVED/intermediate/404/422 cases
- [x] Update FULL_REPOSITORY_REVIEW.md remediation status table and per-finding markers
- **Status**: done
- **Summary**: 246 fast backend tests pass at 98.75% coverage (≥90% gate); 7 ai_eval tests pass; 17 SDK tests pass; 3 frontend tests pass; ruff/black/mypy clean. 8 TDD pairs (test:/feat: or test:/fix:) landed, one per finding. W7 (split historical commits) and W8 (SDK 5xx backoff) deferred per the remediation plan.


### 2026-06-18 — Phase 6: Hardening, Docker, CI/CD, Evaluation, Documentation
- [x] Security: BodySizeLimitMiddleware (413) + CORS allowlist wired from config; bound previously-ignored WATCHDOG_REQUEST_BODY_MAX_BYTES — TDD
- [x] AI eval: classification→root-cause pipeline accuracy test + per-fixture root-cause keywords + deterministic scorecard generator (artifacts/ai_evaluations.md, gitignored)
- [x] Docker: nginx reverse-proxy config, multi-stage frontend image, compose enables frontend with healthchecks + service_healthy dependency, backend HEALTHCHECK; runs with no secrets (mock AI default)
- [x] CI: lint/type/test over backend+tests+sdk+scripts with 90% coverage floor; dedicated ai-eval, frontend build+Vitest, and pip-audit jobs
- [x] Docs: full README rewrite (architecture, API, SDK, Docker, security) + 11-slide Marp deck under deck/
- **Status**: done
- **Summary**: 230 backend tests green (~99% coverage), 3 frontend tests green; ruff/black/mypy clean; docker compose config validated and frontend prod build verified (Docker daemon unavailable for image build). MASTER_PLAN M6 + doc Section 15 acceptance all checked.

### 2026-06-18 — Phase 5: SDK + Synthetic Traffic Generator
- [x] watchdog_client SDK: 6 typed methods (create_event/create_batch/get_incidents/get_incident/get_risk_score/get_alerts), Pydantic models mirroring backend, no backend imports — TDD with respx
- [x] SDK error handling: WatchdogAPIError (4xx/5xx + code), WatchdogTimeout (idempotent GET retries), WatchdogValidationError; API-key header; context manager
- [x] SDK packaging: own sdk/pyproject.toml (semver 0.1.0) + CHANGELOG.md + README.md; `pip install -e sdk`
- [x] Synthetic generator: pure seeded Scenario protocol + 7 scenarios (normal/db_outage/auth_failures/throttling/memory_leak/dependency_failure/black_friday) — TDD
- [x] dependency_failure cascades from data/topology.json (reverse-BFS layers) with JSON fallback; CLI sends via SDK in ≤1000 batches with --seed/--duration/--api-url/--dry-run
- **Status**: done
- **Summary**: 223 tests pass; SDK 15 respx-mocked tests, generator 31 tests (97–99% coverage); ruff/black/mypy clean across backend+sdk+scripts. CLI verified as `python -m scripts.synth.cli`. SDK is standalone (no backend import); scenarios deterministic given a seed.

### 2026-06-18 — Phase 4: Alerts + Topology + Dashboard
- [x] Alert model + repository; 4 simulated channels (dashboard/webhook/email/slack); AlertService fan-out with dedup + rate-limit per incident+channel; sanitized payloads — TDD
- [x] ServiceTopology model + repository + idempotent JSON seeder (data/topology.json); TopologyEngine blast radius (reverse-BFS) + root service — TDD
- [x] PipelineService: detect → correlate → one-shot triage → alert; wired into POST /events[/batch] via DI (Mock AI default, Gemini when configured) — TDD
- [x] Persist recommended_actions + runbook_references on incident; GET /api/v1/alerts + GET /api/v1/topology (incident-aware blast radius); risk score counts open alerts; /metrics expanded — TDD
- [x] React + Vite + TS dashboard (TanStack Query): Overview, Incident Center, AI Analysis, Topology; 3 Vitest behavioral tests
- **Status**: done
- **Summary**: 180 backend tests pass (incl. ai_eval), 97% coverage on Phase 4 modules; ruff/black/mypy green. Frontend builds + 3 behavioral tests pass. Runtime smoke confirms topology seed + live endpoints. End-to-end pipeline proven at service level (storm → triaged incident + alerts + risk drop).

### 2026-06-18 — Phase 3: Agentic Triage + RAG
- [x] LLMClient protocol + FakeLLMClient (test double) + GeminiLLMClient (only google.genai importer) + MockAIClient (offline heuristic) — TDD
- [x] LLMEvaluation ORM model + repository; PromptLog records every call to llm_evaluations + appends docs/llm_prompts.md — TDD
- [x] RAG: RunbookLoader (YAML frontmatter), HashingEmbedder (deterministic BoW), RunbookRetriever (cosine top-k + floor + tie-break) + 5 seed runbooks — TDD
- [x] StructuredAgent base (timing/logging/fallback DRY) + Classification/RootCause/Remediation/ExecutiveSummary agents; versioned prompts; sanitize (prompt-injection) — TDD
- [x] TriageService orchestration: classify -> root cause -> RAG -> remediation (cites runbook) -> exec summary; persists category/root_cause/summary/confidence — TDD
- [x] AI eval suite: 5 fixtures + classification accuracy (100% ≥ 80%) + remediation-cites-runbook (@ai_eval)
- [x] fake_llm fixture; pyyaml + types-PyYAML deps; mypy override for google.genai
- **Status**: done
- **Summary**: 147 tests pass (incl. ai_eval), 99% coverage; ruff/black/mypy green. Only GeminiLLMClient touches google.genai; every agent output is a validated Pydantic schema; agents fall back deterministically (confidence 0.0) so triage never crashes. Triage HTTP endpoint + runtime DI provider deferred to Phase 4 (pipeline/dashboard), consistent with Phase 2.

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
