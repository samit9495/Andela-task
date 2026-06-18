"""Tests for WatchdogClient. HTTP is mocked at the boundary with respx."""

from datetime import UTC, datetime

import httpx
import pytest
import respx

from watchdog_client import (
    EventCreate,
    WatchdogAPIError,
    WatchdogClient,
    WatchdogTimeout,
)
from watchdog_client.models import AlertRead, EventRead, HealthStatus, IncidentRead, RiskScore

BASE = "http://test"
_NOW = datetime(2026, 6, 18, 10, 0, 0, tzinfo=UTC)


def _client() -> WatchdogClient:
    return WatchdogClient(base_url=BASE)


def _event() -> EventCreate:
    return EventCreate(service="payment-api", level="ERROR", message="boom", timestamp=_NOW)


def _incident_json(incident_id: int = 1) -> dict:
    return {
        "id": incident_id,
        "title": "DB outage",
        "service": "payment-api",
        "category": "database",
        "severity": "CRITICAL",
        "status": "OPEN",
        "root_cause": None,
        "summary": None,
        "confidence_score": None,
        "recommended_actions": None,
        "runbook_references": None,
        "created_at": "2026-06-18T10:00:00Z",
        "updated_at": "2026-06-18T10:00:00Z",
        "resolved_at": None,
        "anomalies": [],
    }


@respx.mock
def test_create_event_posts_and_returns_typed():
    route = respx.post(f"{BASE}/api/v1/events").mock(
        return_value=httpx.Response(
            201,
            json={
                "id": 7,
                "service": "payment-api",
                "level": "ERROR",
                "message": "boom",
                "signature": "boom",
                "timestamp": "2026-06-18T10:00:00Z",
                "created_at": "2026-06-18T10:00:00Z",
            },
        )
    )

    result = _client().create_event(_event())

    assert route.called
    assert isinstance(result, EventRead)
    assert result.id == 7


@respx.mock
def test_create_batch_posts_and_returns_result():
    route = respx.post(f"{BASE}/api/v1/events/batch").mock(
        return_value=httpx.Response(201, json={"created": 2, "event_ids": [1, 2]})
    )

    result = _client().create_batch([_event(), _event()])

    assert route.called
    assert result.created == 2
    assert result.event_ids == [1, 2]


@respx.mock
def test_get_incidents_returns_typed_list_with_filters():
    route = respx.get(f"{BASE}/api/v1/incidents").mock(
        return_value=httpx.Response(200, json=[_incident_json()])
    )

    result = _client().get_incidents(status="OPEN", severity="CRITICAL")

    assert route.called
    assert route.calls.last.request.url.params["status"] == "OPEN"
    assert len(result) == 1
    assert isinstance(result[0], IncidentRead)


@respx.mock
def test_get_incident_returns_typed():
    respx.get(f"{BASE}/api/v1/incidents/1").mock(
        return_value=httpx.Response(200, json=_incident_json())
    )

    result = _client().get_incident(1)

    assert isinstance(result, IncidentRead)
    assert result.id == 1


@respx.mock
def test_get_incident_404_raises_api_error():
    respx.get(f"{BASE}/api/v1/incidents/99").mock(
        return_value=httpx.Response(404, json={"detail": "nope", "code": "incident_not_found"})
    )

    with pytest.raises(WatchdogAPIError) as exc:
        _client().get_incident(99)

    assert exc.value.status_code == 404
    assert exc.value.code == "incident_not_found"


@respx.mock
def test_get_risk_score_returns_typed():
    respx.get(f"{BASE}/api/v1/risk-score").mock(
        return_value=httpx.Response(
            200,
            json={
                "score": 72.5,
                "status": "Warning",
                "error_penalty": 10.0,
                "alert_penalty": 5.0,
                "incident_penalty": 12.5,
            },
        )
    )

    result = _client().get_risk_score()

    assert isinstance(result, RiskScore)
    assert result.status == "Warning"


@respx.mock
def test_get_alerts_filters_by_incident():
    route = respx.get(f"{BASE}/api/v1/alerts").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "id": 1,
                    "incident_id": 3,
                    "channel": "webhook",
                    "status": "SENT",
                    "dedup_key": "3:webhook",
                    "payload": {"incident_id": 3},
                    "created_at": "2026-06-18T10:00:00Z",
                }
            ],
        )
    )

    result = _client().get_alerts(incident_id=3)

    assert route.calls.last.request.url.params["incident_id"] == "3"
    assert isinstance(result[0], AlertRead)


@respx.mock
def test_4xx_raises_watchdog_api_error_with_code():
    respx.post(f"{BASE}/api/v1/events").mock(
        return_value=httpx.Response(422, json={"detail": "bad", "code": "event_validation_error"})
    )

    with pytest.raises(WatchdogAPIError) as exc:
        _client().create_event(_event())

    assert exc.value.status_code == 422
    assert exc.value.code == "event_validation_error"


@respx.mock
def test_timeout_raises_watchdog_timeout():
    respx.get(f"{BASE}/api/v1/risk-score").mock(side_effect=httpx.ConnectTimeout("slow"))

    with pytest.raises(WatchdogTimeout):
        _client().get_risk_score()


@respx.mock
def test_get_retries_then_succeeds():
    route = respx.get(f"{BASE}/api/v1/risk-score").mock(
        side_effect=[
            httpx.ConnectError("dropped"),
            httpx.Response(
                200,
                json={
                    "score": 100.0,
                    "status": "Healthy",
                    "error_penalty": 0.0,
                    "alert_penalty": 0.0,
                    "incident_penalty": 0.0,
                },
            ),
        ]
    )

    result = WatchdogClient(base_url=BASE, max_retries=1).get_risk_score()

    assert result.status == "Healthy"
    assert route.call_count == 2


@respx.mock
def test_api_key_sent_as_header():
    route = respx.get(f"{BASE}/api/v1/alerts").mock(return_value=httpx.Response(200, json=[]))

    WatchdogClient(base_url=BASE, api_key="secret-key").get_alerts()

    assert route.calls.last.request.headers["X-API-Key"] == "secret-key"


@respx.mock
def test_get_health_returns_typed():
    respx.get(f"{BASE}/health").mock(
        return_value=httpx.Response(
            200, json={"status": "ok", "version": "0.1.0", "ai_mode": "mock"}
        )
    )

    result = _client().get_health()

    assert isinstance(result, HealthStatus)
    assert result.status == "ok"
    assert result.version == "0.1.0"
    assert result.ai_mode == "mock"


@respx.mock
def test_get_health_raises_on_timeout():
    respx.get(f"{BASE}/health").mock(side_effect=httpx.ConnectTimeout("slow"))

    with pytest.raises(WatchdogTimeout):
        _client().get_health()


@respx.mock
def test_context_manager_closes_without_error():
    respx.get(f"{BASE}/api/v1/risk-score").mock(
        return_value=httpx.Response(
            200,
            json={
                "score": 100.0,
                "status": "Healthy",
                "error_penalty": 0.0,
                "alert_penalty": 0.0,
                "incident_penalty": 0.0,
            },
        )
    )

    with WatchdogClient(base_url=BASE) as client:
        assert client.get_risk_score().score == 100.0
