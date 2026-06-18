---
name: andela-sdk-client
description: Build/extend the watchdog_client Python SDK test-first — typed methods, semantic versioning, mocked HTTP, decoupled from the backend.
---

# Andela SDK Client (`watchdog_client`)

## Trigger

Use when asked to: add an SDK method, mirror a new backend endpoint, fix an SDK bug, version-bump the SDK.

## Context

The SDK (Req. doc Section 7) is a thin, typed Python client that wraps the platform API. It ships in `sdk/` with its **own** `pyproject.toml` and **its own semver**. It must not import from `backend.app`.

## Step 0 — RED: failing test for a new SDK method

```python
# sdk/tests/test_client.py
import httpx, respx
from watchdog_client import WatchdogClient
from watchdog_client.models import IncidentRead


@respx.mock
def test_get_incidents_returns_typed_list():
    route = respx.get("http://localhost:8000/api/v1/incidents").mock(
        return_value=httpx.Response(200, json=[
            {
                "id": 1, "title": "DB outage", "severity": "high", "status": "open",
                "created_at": "2026-06-18T10:00:00Z", "resolved_at": None,
                "root_cause": None, "summary": None,
            }
        ])
    )
    client = WatchdogClient(base_url="http://localhost:8000")
    result = client.get_incidents()
    assert route.called
    assert len(result) == 1
    assert isinstance(result[0], IncidentRead)
    assert result[0].id == 1


@respx.mock
def test_get_incidents_raises_watchdog_api_error_on_4xx():
    respx.get("http://localhost:8000/api/v1/incidents").mock(
        return_value=httpx.Response(400, json={"detail": "bad", "code": "bad_request"})
    )
    with pytest.raises(WatchdogAPIError) as exc:
        WatchdogClient(base_url="http://localhost:8000").get_incidents()
    assert exc.value.status_code == 400
    assert exc.value.code == "bad_request"
```

Run it, fail it, commit `test: ...`.

## Step 1 — Define the Pydantic models (mirror the backend)

```python
# sdk/watchdog_client/models.py
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict


class IncidentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    severity: Literal["critical", "high", "medium", "low"]
    status: Literal["open", "investigating", "mitigated", "resolved"]
    created_at: datetime
    resolved_at: datetime | None = None
    root_cause: str | None = None
    summary: str | None = None
```

These mirror the backend Pydantic schemas. **Drift is a bug.**

## Step 2 — Implement the method on the client

```python
# sdk/watchdog_client/client.py
import httpx
from typing import Any
from .models import IncidentRead, EventCreate
from .exceptions import WatchdogAPIError, WatchdogTimeout


class WatchdogClient:
    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        timeout: float = 5.0,
        max_retries: int = 2,
    ):
        self._client = httpx.Client(
            base_url=base_url,
            timeout=timeout,
            headers={"X-API-Key": api_key} if api_key else {},
        )
        self._max_retries = max_retries

    def get_incidents(
        self,
        *,
        status: str | None = None,
        severity: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[IncidentRead]:
        """Return paginated incidents.

        :raises WatchdogAPIError: on 4xx/5xx responses.
        :raises WatchdogTimeout: on connection timeouts.
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if status: params["status"] = status
        if severity: params["severity"] = severity
        resp = self._get("/api/v1/incidents", params=params)
        return [IncidentRead.model_validate(item) for item in resp.json()]

    def _get(self, path: str, *, params: dict | None = None) -> httpx.Response:
        try:
            resp = self._client.get(path, params=params)
        except httpx.TimeoutException as exc:
            raise WatchdogTimeout(str(exc)) from exc
        if resp.status_code >= 400:
            try:
                payload = resp.json()
                raise WatchdogAPIError(resp.status_code, payload.get("code", "unknown"), payload.get("detail", ""))
            except ValueError:
                raise WatchdogAPIError(resp.status_code, "unknown", resp.text or "")
        return resp
```

## Step 3 — Public API surface

`sdk/watchdog_client/__init__.py` re-exports **only** the public surface:

```python
from .client import WatchdogClient
from .models import EventCreate, IncidentRead, AlertRead, RiskScore
from .exceptions import WatchdogError, WatchdogAPIError, WatchdogTimeout, WatchdogValidationError

__all__ = [
    "WatchdogClient",
    "EventCreate", "IncidentRead", "AlertRead", "RiskScore",
    "WatchdogError", "WatchdogAPIError", "WatchdogTimeout", "WatchdogValidationError",
]
```

## Step 4 — Run tests, commit GREEN, refactor

```bash
pytest sdk/tests -v
git add sdk/
git commit -m "feat(sdk): get_incidents returns typed list"
```

## Step 5 — Versioning (semver) and changelog

For any user-visible change:

| Change | Bump |
|--------|------|
| New method or new optional parameter | minor (`1.2.0` → `1.3.0`) |
| Breaking signature / removed field | major (`1.x` → `2.0.0`) |
| Bug fix, no contract change | patch (`1.2.0` → `1.2.1`) |

Update `sdk/pyproject.toml` and `sdk/CHANGELOG.md` in the same commit.

## Step 6 — README example

`sdk/README.md` must show the method in use:

```python
from watchdog_client import WatchdogClient

client = WatchdogClient(base_url="http://localhost:8000")
incidents = client.get_incidents(status="open", limit=20)
for inc in incidents:
    print(inc.id, inc.severity, inc.title)
```

## Anti-patterns

- `from backend.app... import ...` inside the SDK. The SDK is a separate package.
- Embedding business logic ("if status is open, sleep and retry"). The SDK calls the API.
- Catching all exceptions and returning `None`. Raise SDK exceptions; the caller decides.
- Logging the API key.
- A method without a docstring or example.

## Checklist

- [ ] Failing test (with `respx`) added first
- [ ] Pydantic model in `sdk/watchdog_client/models.py` mirrors the backend schema
- [ ] Method has full type hints and a docstring with `:raises:` clauses
- [ ] 4xx → `WatchdogAPIError`, timeout → `WatchdogTimeout`
- [ ] Public exports updated in `__init__.py`
- [ ] `pyproject.toml` version bumped per semver rules
- [ ] `sdk/CHANGELOG.md` and `sdk/README.md` updated

## See also

- Rule: `.cursor/rules/andela-sdk.mdc`
- Rule: `.cursor/rules/andela-api-routes.mdc` (the contract you mirror)
- Rule: `.cursor/rules/andela-testing.mdc` (testing rules apply to the SDK)
- Skill: `.cursor/skills/andela-tdd-loop/SKILL.md`
