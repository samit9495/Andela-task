# Changelog

All notable changes to `watchdog_client` are documented here. This project
adheres to [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-06-18

### Added
- `WatchdogClient` with six typed methods: `create_event`, `create_batch`,
  `get_incidents`, `get_incident`, `get_risk_score`, `get_alerts`.
- Typed Pydantic models mirroring the platform API (`EventCreate`, `EventRead`,
  `BatchEventResult`, `IncidentRead`, `AnomalyRead`, `RunbookReference`,
  `AlertRead`, `RiskScore`).
- Error handling: `WatchdogAPIError` (4xx/5xx with `status_code`/`code`),
  `WatchdogTimeout` (timeout/transport failure), `WatchdogValidationError`.
- Idempotent GET retries; API-key header support; context-manager support.
