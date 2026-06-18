# watchdog_client

A thin, typed Python SDK for the **Agentic Observability Platform** API. It is a
standalone package with its own semantic version and does not depend on the
backend.

## Install

```bash
pip install -e sdk
```

## Usage

```python
from datetime import datetime, timezone

from watchdog_client import WatchdogClient, EventCreate

client = WatchdogClient(base_url="http://localhost:8000")

# Ingest events
client.create_event(
    EventCreate(
        service="payment-api",
        level="ERROR",
        message="Database timeout after 20s",
        timestamp=datetime.now(tz=timezone.utc),
    )
)

# Query the platform
for incident in client.get_incidents(status="OPEN"):
    print(incident.id, incident.severity, incident.title)

risk = client.get_risk_score()
print(risk.score, risk.status)

for alert in client.get_alerts():
    print(alert.channel, alert.incident_id)
```

## Methods

| Method | Endpoint |
|--------|----------|
| `create_event(event)` | `POST /api/v1/events` |
| `create_batch(events)` | `POST /api/v1/events/batch` |
| `get_incidents(status=, severity=)` | `GET /api/v1/incidents` |
| `get_incident(id)` | `GET /api/v1/incidents/{id}` |
| `get_risk_score()` | `GET /api/v1/risk-score` |
| `get_alerts(incident_id=)` | `GET /api/v1/alerts` |

## Errors

- `WatchdogAPIError` — a 4xx/5xx response (`status_code`, `code`, `detail`).
- `WatchdogTimeout` — connection timeout or transport failure after retries.
- `WatchdogValidationError` — response did not match the expected schema.

## Versioning

Semantic Versioning. New method / optional param → minor; breaking change →
major; bug fix → patch. See [`CHANGELOG.md`](CHANGELOG.md).
