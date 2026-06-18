# `.cursor/plan/`

Workspace archive of every plan produced by Cursor's plan mode (`CreatePlan`).

## Convention

- One file per plan: `<plan-name>.plan.md` (kebab-case).
- Drop the random hash suffix that `CreatePlan` appends to the global filename (e.g. `migration-docs_6ffebcb7.plan.md` -> `migration-docs.plan.md`).
- Keep the frontmatter (`name`, `overview`, `todos`, `isProject`) intact so future agents can re-load context.
- Commit the file alongside the work it produced (`docs(plan): archive <plan-name>`).

## Why this folder exists

Cursor's `CreatePlan` tool writes to the global path `~/.cursor/plans/<plan>_<hash>.plan.md`, which is **not** tracked by git and is invisible to anyone else who clones the repo. This folder is the project-local, version-controlled copy that future contributors (and agents) can rely on.

## Workflow

1. Plan mode produces a plan at `~/.cursor/plans/<name>_<hash>.plan.md`.
2. After the plan is approved (or after the work it describes is complete), copy the file to `.cursor/plan/<name>.plan.md` in this workspace.
3. Update the frontmatter `todos[*].status` to reflect the final outcome.
4. Commit it.

See [`.cursor/rules/ai-workflow.mdc`](../rules/ai-workflow.mdc) for the canonical rule.
