---
name: andela-synthetic-traffic
description: Generate the 7 demo scenarios for the synthetic traffic generator — normal, DB outage, auth failures, throttling, memory leak, dependency failure, Black Friday. Deterministic, test-driven.
---

# Andela Synthetic Traffic

## Trigger

Use when asked to: generate demo data, build the traffic generator, simulate a scenario, run the demo.

## Context

The Synthetic Traffic Generator (Req. doc Component 3) creates realistic demo scenarios so the platform can be exercised end-to-end without a real production feed. The 7 required scenarios:

1. **Normal traffic** — mostly INFO with sparse WARN/ERROR.
2. **Database outage** — cluster of `Database timeout` / `Connection refused` ERRORs across services that depend on the DB.
3. **Authentication failures** — burst of `JWT verification failed` and `401 Unauthorized` events on the auth service.
4. **API throttling** — `429 Too Many Requests` spikes on the gateway.
5. **Memory leak** — slow rise in WARN/ERROR over a long window on one service.
6. **Service dependency failure** — root failure on `auth-api` cascading to `order-api` and `payment-api` per the topology.
7. **Black Friday traffic spike** — overall volume increase, mostly INFO but with a higher absolute ERROR count.

Each scenario produces events at all four levels (INFO / WARN / ERROR / CRITICAL) where appropriate.

## Step 0 — Define the scenario interface

```python
# scripts/synth/scenarios/base.py
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable


@dataclass(frozen=True)
class GeneratedEvent:
    service: str
    level: str
    message: str
    timestamp: datetime
    metadata: dict | None = None


class Scenario(Protocol):
    name: str

    def generate(
        self,
        *,
        start: datetime,
        duration_seconds: int,
        rng: random.Random,
    ) -> Iterable[GeneratedEvent]: ...
```

## Step 1 — RED: smallest failing test for the generator runner

```python
# tests/unit/test_synth_traffic.py
class TestSyntheticTrafficRunner:
    def test_normal_scenario_produces_only_info_warn_levels_majority_info(self):
        rng = random.Random(42)
        events = list(NormalScenario().generate(
            start=datetime(2026, 6, 18, 10, 0, tzinfo=timezone.utc),
            duration_seconds=60,
            rng=rng,
        ))
        assert len(events) > 0
        info_count = sum(1 for e in events if e.level == "INFO")
        assert info_count / len(events) >= 0.85
        assert all(e.level in {"INFO", "WARN", "ERROR"} for e in events)

    def test_runner_is_deterministic_with_same_seed(self):
        params = dict(start=..., duration_seconds=60)
        a = list(NormalScenario().generate(rng=random.Random(42), **params))
        b = list(NormalScenario().generate(rng=random.Random(42), **params))
        assert a == b
```

Run it, fail it, commit `test: ...`.

## Step 2 — Implement scenarios one-by-one

Each scenario gets its own RED → GREEN → REFACTOR triple. Keep scenarios small (< 100 lines) and isolated.

```python
# scripts/synth/scenarios/database_outage.py
class DatabaseOutageScenario:
    name = "database_outage"

    def generate(self, *, start, duration_seconds, rng):
        services = ["payment-api", "order-api", "user-api"]
        for second in range(duration_seconds):
            ts = start + timedelta(seconds=second)
            # Background INFO traffic
            for svc in services:
                if rng.random() < 0.3:
                    yield GeneratedEvent(svc, "INFO", "request handled", ts)
            # The outage burst (after second 10, peak at 20-40)
            if 10 <= second <= 50:
                burst_intensity = self._burst_curve(second)
                for _ in range(burst_intensity):
                    svc = rng.choice(services)
                    yield GeneratedEvent(
                        svc, "ERROR",
                        rng.choice(["Database timeout after 20 seconds",
                                    "Connection refused", "Pool exhausted"]),
                        ts,
                    )
```

## Step 3 — CLI

```python
# scripts/synth/cli.py
import argparse, random
from datetime import datetime, timezone
from watchdog_client import WatchdogClient

SCENARIOS = {
    "normal": NormalScenario,
    "db_outage": DatabaseOutageScenario,
    "auth_failures": AuthFailuresScenario,
    "throttling": ThrottlingScenario,
    "memory_leak": MemoryLeakScenario,
    "dependency_failure": DependencyFailureScenario,
    "black_friday": BlackFridayScenario,
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("scenario", choices=list(SCENARIOS))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--duration", type=int, default=120)
    parser.add_argument("--api-url", default="http://localhost:8000")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    scenario = SCENARIOS[args.scenario]()
    client = WatchdogClient(base_url=args.api_url)

    events = list(scenario.generate(
        start=datetime.now(tz=timezone.utc),
        duration_seconds=args.duration,
        rng=rng,
    ))
    # Send in batches of 1000 (max batch size)
    for batch in _chunked(events, 1000):
        client.create_batch(batch)


if __name__ == "__main__":
    main()
```

## Step 4 — Determinism

- Every scenario takes a `random.Random` instance — never call module-level `random.*`.
- The CLI accepts `--seed` (default 42).
- Tests assert that the same seed produces the same event list.

## Step 5 — Topology-aware scenarios

For the `dependency_failure` scenario, read the topology from `data/topology.json` (the same one the platform uses) and propagate failures down the dependency chain with realistic delays.

## Step 6 — All 7 scenarios

Each gets its own file:

```
scripts/synth/scenarios/
├── base.py
├── normal.py
├── database_outage.py
├── auth_failures.py
├── throttling.py
├── memory_leak.py
├── dependency_failure.py
└── black_friday.py
```

## Anti-patterns

- Module-level `random.choice(...)`. Inject a seeded `Random`.
- Using `datetime.now()` inside the scenario without a `start` parameter — kills determinism.
- A 500-line scenario file. Each scenario is small and focused.
- Scenarios that bypass the SDK and `POST` directly. Use `WatchdogClient`.
- Hardcoding service names that disagree with `data/topology.json`.

## Checklist

- [ ] Each scenario in its own file under `scripts/synth/scenarios/`
- [ ] Each scenario is deterministic given a `random.Random`
- [ ] Each scenario produces events at the appropriate levels (INFO/WARN/ERROR/CRITICAL)
- [ ] The CLI accepts `--seed`, `--duration`, `--api-url`, and the scenario name
- [ ] Events are POSTed via `watchdog_client` (not raw `requests`)
- [ ] Tests assert: produces events, levels match, deterministic with seed
- [ ] Documented in `scripts/synth/README.md` with one-line per scenario

## See also

- Rule: `.cursor/rules/andela-project-map.mdc`
- Rule: `.cursor/rules/andela-sdk.mdc` (the SDK used to send events)
- Skill: `.cursor/skills/andela-tdd-loop/SKILL.md`
- Skill: `.cursor/skills/andela-sdk-client/SKILL.md`
