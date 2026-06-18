---
name: andela-tdd-loop
description: The one-screen Red-Green-Refactor-Commit recipe. Read this at the start of every behavior change. The default workflow for the Andela assessment.
---

# Andela TDD Loop

## Trigger

Use when asked to: `TDD: <behavior>`, `RED:`, `GREEN:`, `REFACTOR:`, or any prompt that requests new behavior, a bug fix, or a refactor. **If you are about to write production code, run this skill first.**

## Context

The Andela Agentic Observability Platform assessment is graded on the visible TDD evolution in `git log`. This skill produces a commit history that looks like:

```
abc1234 test: ingestion endpoint accepts a single log event
def5678 feat: implement POST /api/v1/events for single event
9abcde0 refactor: extract event normalization helper
```

Every step gets its own commit. The assessor can replay the design decisions.

## The loop

### Step 1 — RED: write the smallest failing test

Pick the next observable behavior. Write the test that proves it does not work yet.

```python
# tests/unit/test_detection_z_score.py
def test_z_score_detector_returns_empty_when_baseline_is_constant(self, db):
    detector = ZScoreDetector(threshold=3.0)
    ctx = DetectionContext(baseline_rates=[10, 10, 10, 10], current_rate=10)
    assert detector.detect(ctx) == []
```

Constraints:

- One assertion (or one tightly coupled set of assertions about the same fact).
- The test must fail because the behavior is missing, not because of a typo or import error.
- If it fails to compile / import — that **counts as a failure** per the second law of TDD. Move on once compilation alone produces a clear failure.

### Step 2 — Run it and confirm it fails

```bash
pytest tests/unit/test_detection_z_score.py -k constant -v
```

Paste the failure into the chat. If it does not fail — you did not understand the behavior. Start over.

### Step 3 — Commit the RED

```bash
git add tests/unit/test_detection_z_score.py
git commit -m "test: z-score detector returns empty when baseline is constant"
```

The commit message uses the `test:` prefix. The body (optional) can name the file and the behavior in one line.

### Step 4 — GREEN: minimum code to pass

Write the **least** production code that makes the test pass. No more.

```python
# backend/app/detection/strategies/error_rate_z_score.py
class ZScoreDetector:
    def __init__(self, threshold: float):
        self.threshold = threshold

    def detect(self, ctx):
        return []
```

Yes, this is "wrong" in the long run. It will get fixed in the next RED step. The Third Law forbids writing more.

### Step 5 — Run all tests; confirm green

```bash
pytest -v
```

Paste the pass. If anything else broke, fix the smallest possible thing or revert.

### Step 6 — Commit the GREEN

```bash
git add backend/app/detection/strategies/error_rate_z_score.py
git commit -m "feat: scaffold ZScoreDetector returning no anomalies"
```

`feat:` for new behavior, `fix:` for a regression test that proved a bug, `chore:` only if the production change is purely scaffolding.

### Step 7 — REFACTOR (optional, but encouraged)

If the code or the test can be cleaner without changing behavior:

- Rename variables.
- Extract helpers.
- Push behavior onto the right object.
- Eliminate duplication that now exists between this and previous code.

Re-run all tests after every micro-step. If anything breaks, undo and try a smaller refactor. If nothing changed: skip this step, no commit.

### Step 8 — Commit the REFACTOR

```bash
git add -A
git commit -m "refactor: extract DetectionContext dataclass"
```

`refactor:` commits never add tests and never change behavior.

### Step 9 — Artifact audit (60-second check)

Before looping back, ask whether the commit(s) you just made should update any of these. Most loops produce **none** — that is correct.

| Trigger in the commit | Where to record |
|-----------------------|------------------|
| A design decision picked among real alternatives | `docs/tradeoffs.md` |
| A perf measurement, or any `perf:` commit | `docs/performance.md` |
| **Any LLM prompt that shipped or changed** | **`docs/llm_prompts.md` (mandatory — Req. doc Section 15)** |
| A new agent, detector, or runbook | Update `andela-project-map.mdc` |

> Human instructions are logged automatically to `docs/prompts.md` by the
> `beforeSubmitPrompt` hook — no manual step needed for that file.

If yes, append the entry and commit:

```bash
git add docs/
git commit -m "docs(prompts): record classification agent v1 prompt"
```

If no, continue.

### Step 10 — Loop back

Pick the next behavior. Often the current "no anomalies" stub does not match the next test, so the next RED step will be:

```python
def test_z_score_detector_returns_anomaly_when_current_exceeds_threshold(self):
    detector = ZScoreDetector(threshold=3.0)
    ctx = DetectionContext(baseline_rates=[10, 11, 9, 12, 10, 11], current_rate=70)
    anomalies = detector.detect(ctx)
    assert len(anomalies) == 1
    assert anomalies[0].score > 3.0
```

…and so on.

## Anti-patterns this skill prevents

- Writing the implementation first and then "adding tests" — the test was not failing for the right reason.
- Bundling test + implementation + refactor into one commit — the assessor cannot read the design decisions.
- Writing five tests up-front for a feature — overcommits to a design you have not validated.
- Refactoring while a test is red — you no longer have a safety net.
- Calling the live Gemini API from a unit test — use the `FakeLLMClient` fixture.

## Cross-references

- `.cursor/rules/andela-tdd-discipline.mdc` — the Three Laws and the "what counts as a test" table.
- `.cursor/rules/andela-commit-hygiene.mdc` — message conventions.
- `.cursor/rules/andela-testing.mdc` — pytest layout and fixtures.
- `.cursor/agents/andela-code-reviewer.md` — the git log audit checklist that this skill produces compliant input for.
