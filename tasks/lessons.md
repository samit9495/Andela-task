# Tasks — lessons.md

> Capture anything you learned the hard way. See [`.cursor/rules/ai-workflow.mdc`](../.cursor/rules/ai-workflow.mdc) for the format.
>
> Append at the **top** of the list (most recent first). If a lesson recurs, **promote** it to a `.cursor/rules/` entry.

## Format

```markdown
### YYYY-MM-DD — <short title>
**Context**: What was being done.
**Issue**: What went wrong or was surprising.
**Fix/Insight**: What to do differently next time.
```

## Lessons

### 2026-06-18 — CI `pip-audit` is a no-op without the project installed
**Context**: Security review of the post-remediation `main` branch.
**Issue**: `.github/workflows/ci.yml` `security` job installs only `pip-audit`, then runs it — but the project (and thus `fastapi`, `starlette`, etc.) is never installed in that job. `pip-audit` only sees its own deps, so the 7 starlette CVEs in `pyproject.toml` would never have surfaced in CI.
**Fix/Insight**: Any future `pip-audit` / `safety` CI job MUST install the project first (`pip install -e ".[dev]"`) or it's cosmetic. Generally: for any "scanner" CI step, verify it actually has eyes on the artifact you think it does — run it locally on the same artifact and compare counts.

### 2026-06-18 — "Now" must come from `date -u` at report time, not the `<timestamp>` tag
**Context**: Reporting cumulative elapsed time at the end of Phase 6.
**Issue**: Reported "now 3:56 PM IST" from the turn's `<timestamp>` tag, but the real time was ~4:11 PM. The tag is captured when the user hits *send*, before the turn runs; a long turn (tools/edits/tests) makes it stale by 10–15 min. The previous fix correctly banned *estimating* time but still allowed the (stale) `<timestamp>` tag as the preferred source — that was the remaining bug.
**Fix/Insight**: Always run `date -u +"%Y-%m-%dT%H:%M:%SZ"` as the LAST step before writing an elapsed-time report, and use that value as "now". The `<timestamp>` tag is only a rough lower bound, never "now". Updated `.cursor/rules/andela-time-tracking.mdc` to make `date -u` the sole authoritative current-time source and to explain why the tag is stale.

### 2026-06-18 — Never estimate the current time; read it from the timestamp/date
**Context**: Reporting cumulative elapsed time at the end of Phase 5.
**Issue**: Reported "now ≈ 4:06 PM IST" when the real time was 3:46 PM (writing) / 3:52 PM (now). I extrapolated the current time by mentally adding working time to the last value instead of reading it. This is a different failure from the earlier "sum of phases" bug — here the *start* math was fine but the *current time* was invented and overshot by ~20 min.
**Fix/Insight**: The current time is never reasoned about. Read it verbatim from (1) the turn's `<timestamp>` context tag, or (2) `date -u` run that same turn. Then subtract `start` (`2026-06-18T08:04:59Z`). Quote the raw timestamp used. Strengthened `.cursor/rules/andela-time-tracking.mdc` with a "Never estimate the current time" section.

### 2026-06-18 — Elapsed time must be (now − start), never a sum of phase estimates
**Context**: Reporting cumulative elapsed time toward the 4–6h MVP target at the end of each phase.
**Issue**: Reported "≈ 1h 55m" cumulative when only ~1h 29m of wall-clock had passed since the 1:35 PM IST start. Recurring error (also happened in Phase 1). Root cause: I summed per-phase deltas (each rounded up and inflated by thinking/tool time), so the total exceeded real wall-clock — which is impossible.
**Fix/Insight**: Cumulative elapsed is ALWAYS a single subtraction: `current UTC − start UTC`. Get both authoritatively: start = first real prompt in `docs/prompts.md` (`2026-06-18T08:04:59Z` = 1:35 PM IST; ignore the earlier `bootstrap` entry), current = `date -u`. Never add rounded per-phase numbers to get a cumulative. A per-phase figure may be `(this phase's prompt ts) − (previous phase's prompt ts)`, but the cumulative is the one subtraction from start. Sanity check: cumulative can never exceed `now − start`. Promoted to `.cursor/rules/andela-time-tracking.mdc`.

### 2026-06-18 — GitHub identity is samit9495
**Context**: Working on the Agentic Observability Platform; anything that ends up on GitHub (commits, pushes, PRs, releases, `gh` operations) must be attributed correctly.
**Issue**: The author/owner identity for GitHub operations was not recorded anywhere, risking commits or PRs under the wrong account.
**Fix/Insight**: Always use the GitHub username **`samit9495`** for any work pushed to GitHub. Promoted to a standing rule — see `.cursor/rules/andela-commit-hygiene.mdc`. (Per the safety protocol, do **not** edit local `git config` to enforce this; just target the correct account when pushing / creating PRs / releases.)
