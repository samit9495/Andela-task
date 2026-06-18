# AI Evaluation Reports

Per-branch reports produced by the `andela-qa-automation` agent (Phase 5).
The agent runs the offline triage pipeline (deterministic `MockAIClient`,
`temperature=0.0`, no live Gemini calls) against the fixtures in
[`tests/ai_eval/fixtures/`](../tests/ai_eval/fixtures) and rates each scenario
against the documented threshold.

## 2026-06-18 — `main` — post-remediation (C1 + W1-W6 + W9)

**Prompt versions**: `classification_v1`, `root_cause_v1`, `remediation_v1`,
`executive_summary_v1`. **Embedder**: `HashingEmbedder` (offline).

| Agent | Metric | Result | Threshold | Status |
|-------|--------|--------|-----------|--------|
| classification_v1 | classification_accuracy | **100%** (5/5) | 80% | PASS |
| root_cause_v1 | root_cause_accuracy | **100%** (5/5) | 80% | PASS |
| remediation_v1 | remediation_quality | **100%** (5/5) | 80% | PASS |
| executive_summary_v1 | summary_quality | **100%** (5/5) | 80% | PASS |

### Per-scenario

| Scenario | Expected | Predicted | Classification | Root cause | Remediation | Summary |
|---|---|---|---|---|---|---|
| application logic error | application | application | PASS | PASS | PASS | PASS |
| authentication failures | authentication | authentication | PASS | PASS | PASS | PASS |
| database outage | database | database | PASS | PASS | PASS | PASS |
| memory leak / OOM | infrastructure | infrastructure | PASS | PASS | PASS | PASS |
| network / dependency failure | network | network | PASS | PASS | PASS | PASS |

**Notes**

- `summary_quality` is the new metric introduced for W5; `MockAIClient` now
  honors an explicit `Category:` hint in chained-agent prompts, so the
  summarizer no longer drifts into "database" for every scenario.
- The W1 sanitization fix means injection markers (`### system`,
  `<<<END>>>`, `<|im_start|>`) in event signatures or runbook excerpts are
  redacted before reaching any agent prompt.
- The C1 fix means a real Gemini 429/401/403/5xx no longer crashes a
  triage request: the agent falls back to a deterministic structured output.

The full machine-readable scorecard is regenerated on every CI run into
[`artifacts/ai_evaluations.md`](../artifacts/ai_evaluations.md) (gitignored).
