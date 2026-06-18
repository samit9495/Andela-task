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

### 2026-06-18 — Elapsed time must be (now − start), never a sum of phase estimates
**Context**: Reporting cumulative elapsed time toward the 4–6h MVP target at the end of each phase.
**Issue**: Reported "≈ 1h 55m" cumulative when only ~1h 29m of wall-clock had passed since the 1:35 PM IST start. Recurring error (also happened in Phase 1). Root cause: I summed per-phase deltas (each rounded up and inflated by thinking/tool time), so the total exceeded real wall-clock — which is impossible.
**Fix/Insight**: Cumulative elapsed is ALWAYS a single subtraction: `current UTC − start UTC`. Get both authoritatively: start = first real prompt in `docs/prompts.md` (`2026-06-18T08:04:59Z` = 1:35 PM IST; ignore the earlier `bootstrap` entry), current = `date -u`. Never add rounded per-phase numbers to get a cumulative. A per-phase figure may be `(this phase's prompt ts) − (previous phase's prompt ts)`, but the cumulative is the one subtraction from start. Sanity check: cumulative can never exceed `now − start`. Promoted to `.cursor/rules/andela-time-tracking.mdc`.

### 2026-06-18 — GitHub identity is samit9495
**Context**: Working on the Agentic Observability Platform; anything that ends up on GitHub (commits, pushes, PRs, releases, `gh` operations) must be attributed correctly.
**Issue**: The author/owner identity for GitHub operations was not recorded anywhere, risking commits or PRs under the wrong account.
**Fix/Insight**: Always use the GitHub username **`samit9495`** for any work pushed to GitHub. Promoted to a standing rule — see `.cursor/rules/andela-commit-hygiene.mdc`. (Per the safety protocol, do **not** edit local `git config` to enforce this; just target the correct account when pushing / creating PRs / releases.)
