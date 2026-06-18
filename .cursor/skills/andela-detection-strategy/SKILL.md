---
name: andela-detection-strategy
description: Implement a statistical detection strategy test-first — Z-Score, EWMA, signature frequency, severity drift. Deterministic, NumPy-based, no magic thresholds.
---

# Andela Detection Strategy

## Trigger

Use when asked to: implement a detector, add a detection strategy, tune a threshold, fix a false positive/negative. Triggered by `DETECT:` shortcut.

## Context

The detection engine (Req. doc Component 4) ships with four strategies:

| Strategy | Asks |
|----------|------|
| Error Rate Z-Score | Is errors-per-minute statistically far from baseline? |
| Error Rate EWMA | Is the EWMA drifting up? |
| Signature Frequency | Is a normalized signature firing N× more than baseline? |
| Severity Distribution Drift | Has the (INFO/WARN/ERROR/CRITICAL) mix shifted? |

Each strategy is one file under `backend/app/detection/strategies/`, implementing the `Detector` protocol, deterministic, and unit-testable in isolation.

## Step 0 — Define `DetectionContext` (shared input)

```python
# backend/app/detection/types.py
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class DetectionContext:
    service: str
    now: datetime                   # window end, UTC
    baseline_rates: list[float]     # one rate per baseline bucket
    current_rate: float             # current bucket
    signature_counts_baseline: dict[str, list[int]] | None = None
    signature_counts_current: dict[str, int] | None = None
    severity_baseline: dict[str, float] | None = None  # proportions
    severity_current: dict[str, float] | None = None
```

## Step 1 — RED: failing test for the strategy

```python
# tests/unit/test_detection_z_score.py
from datetime import datetime, timezone
from app.detection.strategies.error_rate_z_score import ZScoreDetector
from app.detection.types import DetectionContext


class TestZScoreDetector:
    def test_returns_empty_when_current_within_one_sigma(self):
        ctx = DetectionContext(
            service="payment-api",
            now=datetime(2026, 6, 18, 10, 0, tzinfo=timezone.utc),
            baseline_rates=[10, 11, 9, 12, 10, 11],
            current_rate=11,
        )
        assert ZScoreDetector(threshold=3.0).detect(ctx) == []

    def test_returns_anomaly_when_current_exceeds_threshold(self):
        ctx = DetectionContext(
            service="payment-api",
            now=datetime(2026, 6, 18, 10, 0, tzinfo=timezone.utc),
            baseline_rates=[10, 11, 9, 12, 10, 11],
            current_rate=70,
        )
        anomalies = ZScoreDetector(threshold=3.0).detect(ctx)
        assert len(anomalies) == 1
        a = anomalies[0]
        assert a.service == "payment-api"
        assert a.strategy == "error_rate_z_score"
        assert a.score > 3.0

    def test_returns_empty_when_baseline_is_empty(self):
        ctx = DetectionContext(service="x", now=..., baseline_rates=[], current_rate=10)
        assert ZScoreDetector(threshold=3.0).detect(ctx) == []

    def test_returns_empty_when_baseline_stddev_is_zero(self):
        ctx = DetectionContext(service="x", now=..., baseline_rates=[10, 10, 10], current_rate=70)
        assert ZScoreDetector(threshold=3.0).detect(ctx) == []
```

Run it. Confirm failure. Commit each test as a separate `test: ...` commit.

## Step 2 — GREEN: minimum implementation

```python
# backend/app/detection/strategies/error_rate_z_score.py
import math
import numpy as np
from app.detection.types import DetectionContext
from app.models.anomaly import Anomaly


class ZScoreDetector:
    name = "error_rate_z_score"

    def __init__(self, threshold: float):
        self.threshold = threshold

    def detect(self, ctx: DetectionContext) -> list[Anomaly]:
        if not ctx.baseline_rates:
            return []
        baseline = np.asarray(ctx.baseline_rates, dtype=np.float64)
        mean = float(baseline.mean())
        std = float(baseline.std(ddof=1)) if len(baseline) > 1 else 0.0
        if std == 0.0 or math.isclose(std, 0.0):
            return []
        z = (ctx.current_rate - mean) / std
        if z <= self.threshold:
            return []
        return [Anomaly(
            service=ctx.service,
            signature=None,
            strategy=self.name,
            score=z,
            detected_at=ctx.now,
            details={"mean": mean, "std": std, "current": ctx.current_rate},
        )]
```

Commit `feat: ...`.

## Step 3 — REFACTOR (optional)

If both `ZScoreDetector` and `EWMADetector` end up sharing a "compute baseline stats" helper, extract it. Run all tests. Commit `refactor: ...`.

## Step 4 — Repeat for each strategy

### EWMA

```python
class EWMADetector:
    name = "error_rate_ewma"

    def __init__(self, alpha: float, drift_threshold: float):
        self.alpha = alpha
        self.drift_threshold = drift_threshold

    def detect(self, ctx: DetectionContext) -> list[Anomaly]:
        # compute EWMA over baseline_rates
        # compare current_rate against EWMA + drift_threshold * std
        ...
```

### Signature Frequency

```python
class SignatureFrequencyDetector:
    name = "signature_frequency"

    def __init__(self, multiplier: float, min_absolute: int):
        self.multiplier = multiplier
        self.min_absolute = min_absolute

    def detect(self, ctx: DetectionContext) -> list[Anomaly]:
        if not ctx.signature_counts_current:
            return []
        anomalies = []
        for sig, current in ctx.signature_counts_current.items():
            history = ctx.signature_counts_baseline.get(sig, []) if ctx.signature_counts_baseline else []
            if not history or current < self.min_absolute:
                continue
            baseline_mean = float(np.mean(history))
            if baseline_mean == 0.0:
                continue
            if current >= self.multiplier * baseline_mean:
                anomalies.append(Anomaly(
                    service=ctx.service, signature=sig, strategy=self.name,
                    score=current / baseline_mean, detected_at=ctx.now,
                    details={"baseline_mean": baseline_mean, "current": current},
                ))
        return anomalies
```

### Severity Distribution Drift

Use a chi-squared goodness-of-fit between current and baseline severity proportions. Skip if total events in window < `MIN_SAMPLE_SIZE`.

## Step 5 — Edge cases (every detector)

Every test file has these:

- Empty baseline → returns `[]`.
- Single-element baseline → returns `[]`.
- Constant baseline (stddev=0) → returns `[]`.
- All-zero baseline (rate detectors) → returns `[]`.
- Negative inputs → asserted away in `DetectionContext.__post_init__`.

## Step 6 — Configuration (no magic numbers)

```python
# backend/app/core/config.py (excerpt)
class DetectionSettings(BaseModel):
    error_rate_z_score_threshold: float = 3.0
    ewma_alpha: float = 0.3
    ewma_drift_threshold: float = 2.5
    signature_burst_multiplier: float = 5.0
    signature_min_absolute: int = 10
    severity_drift_chi_squared: float = 10.83
    severity_min_sample_size: int = 50
```

The `default_detectors()` factory reads these and constructs each strategy.

## Anti-patterns

- A detector that touches the DB. Detectors take a `DetectionContext`; the caller assembles it.
- A detector that calls the LLM. Detection is deterministic stats.
- `if z > 3:` — magic numbers.
- Catching `Exception` and silently returning `[]`. Let it bubble; the test will catch it.
- `time.now()` inside the detector. Receive `now` via the context.

## Checklist

- [ ] One file per strategy under `backend/app/detection/strategies/`
- [ ] Implements the `Detector` protocol (`name`, `detect(ctx) -> list[Anomaly]`)
- [ ] All thresholds are constructor args read from `DetectionSettings`
- [ ] Edge cases tested (empty/single/constant/all-zero baseline)
- [ ] No `random` / `datetime.now()` inside the detector
- [ ] Anomaly carries enough `details` for downstream correlation and triage

## See also

- Rule: `.cursor/rules/andela-detection-engine.mdc`
- Rule: `.cursor/rules/andela-testing.mdc`
- Skill: `.cursor/skills/andela-tdd-loop/SKILL.md`
- Skill: `.cursor/skills/scaffold-service-layer/SKILL.md`
