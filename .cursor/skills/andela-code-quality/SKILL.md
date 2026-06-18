---
name: andela-code-quality
description: Short companion for the smell catalog — concrete patterns to fix on sight. Use during AUDIT or before committing.
---

# Andela Code Quality (skill)

Companion to `.cursor/rules/andela-code-quality.mdc`.

## Quick smell-to-fix table

| Smell | Fix |
|-------|-----|
| `if z > 3` | `if z > ANOMALY_Z_SCORE_THRESHOLD` (named constant or setting) |
| `level == "ERROR"` | `level == LogLevel.ERROR` (Enum) |
| `try: ... except Exception:` | Catch specific exceptions; let unexpected ones bubble |
| Function > 20 lines | Split. Extract helpers named after what they compute. |
| File > 300 lines | Split by responsibility. |
| Boolean param `dry_run=True` | Two functions: `process(...)`, `simulate_process(...)` |
| `print()` for diagnostics | `logger.info(...)` / `logger.debug(...)` |
| Commented-out code | Delete it. Git remembers. |
| `float` for risk scores | `Decimal` (or `float` only with documented precision) |

## Edge-case checklist (every change)

- Empty input (`[]`, `""`, `None`) → defined behavior?
- One-element input → no division by zero?
- Zero matches in a query → returns `[]`, not 500?
- Negative / out-of-range numerics → guarded at the Pydantic boundary?
- Unicode in event messages / log output → handled?
- Naive datetimes → rejected at the Pydantic boundary?
- LLM timeout / rate limit / malformed JSON → fallback path tested?
- 1000-event batch ingestion → enforced and tested?

## Logging hygiene

```python
logger.exception(
    "Detection failed for service=%s window=%s strategy=%s",
    service, window_id, strategy,
)
```

- Include identifiers (service, signature, incident_id, request_id) — never full payloads.
- No PII, no secrets, no raw LLM responses with user data.

## Risk-score / numerical helpers

```python
from decimal import Decimal

RISK_SCORE_MAX = Decimal("100")
RISK_SCORE_SCALE = Decimal("0.01")

def clamp_risk_score(value: Decimal) -> Decimal:
    if value < 0:
        return Decimal("0")
    if value > RISK_SCORE_MAX:
        return RISK_SCORE_MAX
    return value.quantize(RISK_SCORE_SCALE)
```

## Structure rules

- One responsibility per file.
- `__init__.py` is for re-exports, not behavior.
- A circular import is a design smell — split the offending module.
- Detection strategies live one-per-file under `backend/app/detection/strategies/`. Triage agents one-per-file under `backend/app/triage/agents/`.

## See also

- Rule: `.cursor/rules/andela-code-quality.mdc`
- Rule: `.cursor/rules/andela-craftsmanship.mdc`
- Agent: `.cursor/agents/andela-code-reviewer.md`
