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

### 2026-06-18 — GitHub identity is samit9495
**Context**: Working on the Agentic Observability Platform; anything that ends up on GitHub (commits, pushes, PRs, releases, `gh` operations) must be attributed correctly.
**Issue**: The author/owner identity for GitHub operations was not recorded anywhere, risking commits or PRs under the wrong account.
**Fix/Insight**: Always use the GitHub username **`samit9495`** for any work pushed to GitHub. Promoted to a standing rule — see `.cursor/rules/andela-commit-hygiene.mdc`. (Per the safety protocol, do **not** edit local `git config` to enforce this; just target the correct account when pushing / creating PRs / releases.)
