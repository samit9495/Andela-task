---
marp: true
title: Agentic Observability Platform
paginate: true
theme: default
---

# Agentic Observability Platform

AI-powered SRE: ingest → detect → correlate → **triage with agents** → alert → visualize.

Built test-first. Runs fully offline. No secrets required.

---

## The problem

- Modern systems emit **floods of logs**; humans can't watch them all.
- When something breaks, on-call engineers spend the first painful minutes asking:
  - *What broke? Why? What's the blast radius? What do I do?*
- Traditional dashboards **show data**; they don't **reason** about it.

**Goal:** an API-first platform that turns raw logs into a ranked, explained,
actionable incident — automatically.

---

## What it does

1. **Ingest & normalize** log events (single or batched).
2. **Detect** anomalies with deterministic statistics.
3. **Correlate** anomalies into incidents and **score risk**.
4. **Triage** each incident with a 4-agent LLM pipeline + RAG over runbooks.
5. **Alert** through deduplicated, rate-limited channels.
6. **Visualize** health, incidents, AI analysis, and service topology.

---

## Architecture

```
logs ▶ Ingestion ▶ Detection ▶ Correlation ▶ Incident(+risk)
                                               │
                 ┌─────────────────────────────▼─────────────────────────────┐
                 │ Classification ▶ Root Cause ▶ Remediation ▶ Exec Summary    │
                 │            (LLMClient protocol · RAG runbooks)              │
                 └─────────────────────────────┬─────────────────────────────┘
                                               ▼
                              Alerts ▶ Dashboard / SDK
```

Thin routes → services → repositories. The LLM is always behind a protocol.

---

## The agentic triage pipeline

| Agent | Responsibility | Output (Pydantic) |
| --- | --- | --- |
| Classification | Categorize the incident | category + confidence |
| Root Cause | Identify probable cause | root_cause + confidence |
| Remediation | Recommend fixes (RAG-grounded) | actions + runbook refs |
| Executive Summary | One-paragraph brief | executive_summary |

Every output is **schema-validated**; every prompt is **logged** for audit.

---

## Deterministic & safe by design

- **`LLMClient` protocol**: `MockAIClient` (offline heuristic) ↔ `GeminiLLMClient` (live).
- Tests and the demo never call the live API — **deterministic, free, fast**.
- **Prompt-injection defenses**: untrusted log content is sanitized + delimited;
  structured-output validation is the final guard.
- **Security middleware**: body-size 413 limit + CORS allowlist; sanitized errors.

---

## Engineering discipline

- **TDD throughout** — Red → Green → Refactor, visible in `git log`.
- **Conventional Commits**, one logical change each.
- **≥ 90% coverage** gate (currently ~99%); 224 fast tests run in ~2s.
- **CI**: lint + type-check + test, AI-eval, frontend build, `pip-audit`.
- Ruff + Black + Mypy (strict) all green.

---

## AI evaluation

Deterministic offline scorecard (`artifacts/ai_evaluations.md`):

| Metric | Score |
| --- | --- |
| Classification accuracy | 100% |
| Root-cause accuracy | 100% |
| Remediation quality | 100% |

Scored on 5 fixed incident fixtures with `temperature=0.0`. No live calls.

---

## Demo

```bash
docker compose up --build          # dashboard :5173, API :8000

python -m scripts.synth.cli db_outage --duration 120 --seed 42
```

Watch an incident appear, get classified, root-caused, and remediated —
with runbook citations and a blast-radius view on the topology page.

---

## Summary

- API-first, agentic observability that **reasons**, not just charts.
- Offline-capable, secure, and **provably tested**.
- Clean architecture: swappable LLM, swappable detectors, typed boundaries.
- Backend + React dashboard + Python SDK + synthetic traffic generator.

**Thank you.**
