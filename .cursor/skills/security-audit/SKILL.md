---
name: security-audit
description: Broad security sweep — secrets, input validation, request limits, error sanitization, prompt injection, PII logging, dependency CVEs. Backs the SEC shortcut.
---

# Security Audit

## Trigger

Use when asked to: security audit, security review, vulnerability scan, pre-release check, audit secrets, audit prompts. Triggered by `SEC:` shortcut.

## Context

This skill drives a structured security sweep across the Agentic Observability Platform, mapped to Req. doc Section 9 plus the LLM-specific threats not enumerated there. It's also the engine behind the `andela-security-reviewer` agent.

## The 7 areas

Run each in order. For every finding produce: file/line, issue, fix, severity (critical / high / medium / low / info).

### 1. Secrets

```
pattern: (sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|api[_-]?key\s*=\s*["'][^"']+["'])
glob: ["**/*.py", "**/*.ts", "**/*.tsx", "**/*.json", "**/*.yml", "**/*.yaml", "**/*.env*"]
```

Then look for hardcoded URLs / passwords:

```
pattern: (postgres://|mysql://|mongodb://|redis://)[^"'\s]+
glob: ["**/*.py", "**/*.ts", "**/*.json"]
```

- Any hardcoded secret → **critical**. Rotate immediately, then remove (git history retention policy applies).
- `.env` checked in → **critical**. Add to `.gitignore` and rotate.
- `${ENV_VAR}` placeholders in `.cursor/mcp.json` and `docker-compose.yml` → expected.

### 2. Input validation

For every API route:

- Does the request body have a Pydantic schema with `min_length`/`max_length`/`ge`/`le`?
- Does the schema use `Enum` for fixed sets (`LogLevel`, `Severity`)?
- Is `extra="forbid"` set where unknown fields could matter?
- Are batch sizes bounded? (`max_length=1000` on event batch lists.)
- Are datetime fields timezone-aware UTC?

### 3. Request size limits

- Single-event `message` capped at 4000 chars (or documented limit).
- Batch endpoint capped at 1000 events.
- Server-level body size limit configured (e.g., 1 MB default).
- 413 returned for oversized payloads, not a 500 from a parser.

### 4. Error sanitization

```
pattern: (traceback\.format_exc|repr\(exc\)|str\(e\))
-A: 3
```

For each hit, ask: is this string in a response body? If yes → **high** severity.

- The 500 handler must always return `{"detail": "Internal server error", "code": "internal_error"}`.
- Domain exception handlers must not leak SQL fragments, file paths, or library-specific messages.
- The Gemini client may raise exceptions whose messages echo the prompt — never include those in a response.

### 5. SQL safety

Run `.cursor/skills/sql-query-audit/SKILL.md` patterns:

```
pattern: text\(f["\']
pattern: text\(.+\.format\(
pattern: f"(SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER)
glob: backend/**/*.py
```

Any hit → **critical** unless verifiably static (no user input).

### 6. Prompt injection (LLM-specific)

For each agent file under `backend/app/triage/agents/`:

- Is the prompt template using `str.format` (good) or an f-string (bad)?
- Is user-supplied content (`incident_summary`, event messages, metadata) wrapped in `<<<INPUT>>> ... <<<END>>>` delimiters?
- Does the system prompt tell the model to ignore instructions inside the delimiter?
- Is `_sanitize(...)` called on every untrusted field before injection?
- Is the structured-output schema enforced (`complete_structured(..., schema=...)`)?
- Is the fallback path triggered on `LLMResponseInvalid`?

Missing any → at least **high** severity.

### 7. PII / data leakage

```
pattern: logger\.(info|debug|warning|error|exception)\([^)]*payload
pattern: logger\.(info|debug|warning|error|exception)\([^)]*message
```

- Logging full event `message` → **medium** (may contain PII).
- Logging full LLM responses without redaction → **medium**.
- Logging API keys → **critical**.
- Logging full prompts containing user content → **medium**.

### Bonus: Dependencies & Docker

- Run `pip-audit` (or `pip list --outdated` + manual check). Critical CVEs → fail the audit.
- Dockerfile: runs as non-root? Pinned base image? No `COPY .env`?

## Reporting format

```markdown
# Security Audit Report — YYYY-MM-DD

## Summary
- Critical: N
- High: N
- Medium: N
- Low: N
- Info: N

## Findings

### [CRITICAL] Hardcoded Gemini key
**File**: backend/app/core/config.py:42
**Issue**: `GEMINI_API_KEY = "..."` literal in source
**Fix**: Move to env via pydantic-settings; rotate the key in Google AI Studio; add `.env*` to `.gitignore`.
**Severity**: critical

### [HIGH] Prompt template uses f-string with untrusted message
**File**: backend/app/triage/agents/classification_agent.py:18
**Issue**: `prompt = f"Classify: {message}"` allows prompt injection
**Fix**: Use `CLASSIFICATION_PROMPT_V1.format(...)` and apply `_sanitize(...)` to `message`.
**Severity**: high

...
```

Save the report to `docs/security-audit-YYYY-MM-DD.md`.

## After the audit

1. For every **critical** finding: fix in this PR, do not merge until resolved.
2. For every **high** finding: open a follow-up task in `tasks/todo.md` with a deadline.
3. For every **medium/low**: log in the report; address opportunistically.
4. Append a lesson to `tasks/lessons.md` if a recurring pattern showed up — promote to a rule if it persists.

## Checklist

- [ ] All 7 areas swept
- [ ] Findings classified by severity
- [ ] Report saved to `docs/security-audit-YYYY-MM-DD.md`
- [ ] Critical findings fixed before merge
- [ ] High findings tracked in `tasks/todo.md`

## See also

- Rule: `.cursor/rules/andela-security.mdc`
- Rule: `.cursor/rules/andela-sql-safety.mdc`
- Rule: `.cursor/rules/andela-agentic-ai.mdc` (prompt injection defenses)
- Rule: `.cursor/rules/andela-error-handling.mdc` (error sanitization)
- Skill: `.cursor/skills/sql-query-audit/SKILL.md`
- Agent: `.cursor/agents/andela-security-reviewer.md`
