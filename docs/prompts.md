# Prompt Audit Log

Complete history of every instruction given to the AI coding agent for the
Agentic Observability Platform. Appended automatically by the
`beforeSubmitPrompt` Cursor hook (`.cursor/hooks/log-prompt.sh`).

Runtime Gemini prompts from the triage pipeline are logged separately to
`docs/llm_prompts.md` by `backend/app/triage/prompt_log.py`.

## 2026-06-18T07:35:00Z - conversation `bootstrap` - mode `agent`

> Seed entry added manually: this instruction set up the audit hook itself, so it
> predates the hook. Every later prompt is appended automatically.

```text
There is an acceptance criterion: "prompts.md file containing the full audit log
of all instructions." Confirm whether the rules/skills generate this automatically.
If not, set up docs/prompts.md and update it for every prompt.
```
