# Synthetic Traffic Generator

Generates realistic demo traffic and sends it to the platform via the
`watchdog_client` SDK, so the full pipeline (ingest → detect → correlate →
triage → alert) can be exercised without a real production feed.

## Usage

```bash
# Send a database-outage scenario to a running backend
python -m scripts.synth.cli db_outage --duration 120 --seed 42 --api-url http://localhost:8000

# Generate without sending (counts events only)
python -m scripts.synth.cli normal --duration 60 --dry-run
```

## Scenarios

| Name | Description |
|------|-------------|
| `normal` | Mostly INFO with sparse WARN and the occasional ERROR. |
| `db_outage` | Burst of `Database timeout` / `connection refused` errors across DB consumers. |
| `auth_failures` | Burst of `401 Unauthorized` / `JWT verification failed` on `auth-service`. |
| `throttling` | `429 Too Many Requests` spikes on `api-gateway`. |
| `memory_leak` | Slow rise in WARN/ERROR over a long window on `orders-api`. |
| `dependency_failure` | Root failure on `postgres` cascading to dependents per `data/topology.json`. |
| `black_friday` | Large volume increase, mostly INFO but a higher absolute ERROR count. |

## Determinism

Every scenario takes an injected `random.Random`; the CLI exposes `--seed`
(default 42). The same seed produces the same event list, so demos and tests
are reproducible.
