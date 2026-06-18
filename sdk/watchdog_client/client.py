"""The synchronous Watchdog API client."""

from __future__ import annotations

from types import TracebackType
from typing import Any

import httpx
from pydantic import ValidationError

from .exceptions import WatchdogAPIError, WatchdogTimeout, WatchdogValidationError
from .models import (
    AlertRead,
    BatchEventResult,
    EventCreate,
    EventRead,
    HealthStatus,
    IncidentRead,
    RiskScore,
)


class WatchdogClient:
    """A thin, typed client for the Agentic Observability Platform API.

    Example:
        >>> client = WatchdogClient(base_url="http://localhost:8000")
        >>> incidents = client.get_incidents(status="OPEN")
    """

    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        timeout: float = 5.0,
        max_retries: int = 2,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        headers = {"X-API-Key": api_key} if api_key else {}
        self._client = httpx.Client(
            base_url=base_url,
            timeout=timeout,
            headers=headers,
            transport=transport,
        )
        self._max_retries = max_retries

    # --- public API ---------------------------------------------------------

    def create_event(self, event: EventCreate) -> EventRead:
        """Ingest a single event.

        :raises WatchdogAPIError: on a 4xx/5xx response.
        :raises WatchdogTimeout: on a connection timeout.
        """
        response = self._post("/api/v1/events", json=event.model_dump(mode="json"))
        return self._parse(EventRead, response.json())

    def create_batch(self, events: list[EventCreate]) -> BatchEventResult:
        """Ingest a batch of events (server caps at 1000 per request).

        :raises WatchdogAPIError: on a 4xx/5xx response.
        :raises WatchdogTimeout: on a connection timeout.
        """
        payload = {"events": [event.model_dump(mode="json") for event in events]}
        response = self._post("/api/v1/events/batch", json=payload)
        return self._parse(BatchEventResult, response.json())

    def get_incidents(
        self, *, status: str | None = None, severity: str | None = None
    ) -> list[IncidentRead]:
        """List incidents, optionally filtered by status and severity."""
        params: dict[str, Any] = {}
        if status:
            params["status"] = status
        if severity:
            params["severity"] = severity
        response = self._get("/api/v1/incidents", params=params)
        return [self._parse(IncidentRead, item) for item in response.json()]

    def get_incident(self, incident_id: int) -> IncidentRead:
        """Fetch a single incident by id.

        :raises WatchdogAPIError: 404 if the incident does not exist.
        """
        response = self._get(f"/api/v1/incidents/{incident_id}")
        return self._parse(IncidentRead, response.json())

    def get_risk_score(self) -> RiskScore:
        """Return the current platform risk score."""
        response = self._get("/api/v1/risk-score")
        return self._parse(RiskScore, response.json())

    def get_alerts(self, *, incident_id: int | None = None) -> list[AlertRead]:
        """List fired alerts, optionally filtered by incident."""
        params: dict[str, Any] = {}
        if incident_id is not None:
            params["incident_id"] = incident_id
        response = self._get("/api/v1/alerts", params=params)
        return [self._parse(AlertRead, item) for item in response.json()]

    def get_health(self) -> HealthStatus:
        """Return the backend health status (status, version, ai_mode)."""
        response = self._get("/health")
        return self._parse(HealthStatus, response.json())

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> WatchdogClient:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    # --- transport ----------------------------------------------------------

    def _get(self, path: str, *, params: dict[str, Any] | None = None) -> httpx.Response:
        # GET is idempotent, so it is safe to retry on transport failures.
        last_exc: httpx.HTTPError | None = None
        for _ in range(self._max_retries + 1):
            try:
                return self._raise_for_status(self._client.get(path, params=params))
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                last_exc = exc
        raise WatchdogTimeout(str(last_exc))

    def _post(self, path: str, *, json: Any) -> httpx.Response:
        # POST is not retried to avoid duplicate ingestion.
        try:
            response = self._client.post(path, json=json)
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            raise WatchdogTimeout(str(exc)) from exc
        return self._raise_for_status(response)

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> httpx.Response:
        if response.status_code < 400:
            return response
        try:
            payload = response.json()
            raise WatchdogAPIError(
                response.status_code,
                payload.get("code", "unknown"),
                payload.get("detail", ""),
            )
        except ValueError:
            raise WatchdogAPIError(response.status_code, "unknown", response.text or "") from None

    @staticmethod
    def _parse(model: type[Any], data: Any) -> Any:
        try:
            return model.model_validate(data)
        except ValidationError as exc:
            raise WatchdogValidationError(str(exc)) from exc
