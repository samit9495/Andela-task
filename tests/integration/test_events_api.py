"""Integration tests for the events API."""


def _payload(**overrides):
    base = {
        "service": "payment-api",
        "level": "error",
        "message": "Database timeout after 20 seconds",
        "timestamp": "2026-06-18T10:00:00Z",
    }
    base.update(overrides)
    return base


class TestCreateEvent:
    def test_post_single_event_returns_201_with_signature(self, client):
        response = client.post("/api/v1/events", json=_payload())
        body = response.json()

        assert response.status_code == 201
        assert body["id"] is not None
        assert body["level"] == "ERROR"
        assert body["signature"] == "Database timeout after <NUM> seconds"

    def test_naive_timestamp_returns_422(self, client):
        response = client.post("/api/v1/events", json=_payload(timestamp="2026-06-18T10:00:00"))

        assert response.status_code == 422

    def test_message_too_long_returns_422(self, client):
        response = client.post("/api/v1/events", json=_payload(message="x" * 4001))

        assert response.status_code == 422

    def test_unknown_level_returns_422(self, client):
        response = client.post("/api/v1/events", json=_payload(level="bananas"))
        body = response.json()

        assert response.status_code == 422
        assert body["code"] == "event_validation_error"

    def test_extra_field_is_forbidden(self, client):
        response = client.post("/api/v1/events", json=_payload(rogue="x"))

        assert response.status_code == 422


class TestCreateBatch:
    def test_batch_creates_all(self, client):
        events = [_payload(), _payload(message="Connection refused"), _payload(service="auth-api")]

        response = client.post("/api/v1/events/batch", json={"events": events})
        body = response.json()

        assert response.status_code == 201
        assert body["created"] == 3
        assert len(body["event_ids"]) == 3

    def test_batch_over_limit_returns_422(self, client):
        events = [_payload() for _ in range(1001)]

        response = client.post("/api/v1/events/batch", json={"events": events})

        assert response.status_code == 422

    def test_empty_batch_returns_422(self, client):
        response = client.post("/api/v1/events/batch", json={"events": []})

        assert response.status_code == 422


class TestListEvents:
    def test_empty_returns_empty_list(self, client):
        response = client.get("/api/v1/events")

        assert response.status_code == 200
        assert response.json() == []

    def test_returns_persisted_events(self, client):
        client.post("/api/v1/events", json=_payload())
        client.post("/api/v1/events", json=_payload(service="auth-api"))

        assert len(client.get("/api/v1/events").json()) == 2

    def test_filter_by_service(self, client):
        client.post("/api/v1/events", json=_payload(service="payment-api"))
        client.post("/api/v1/events", json=_payload(service="auth-api"))

        results = client.get("/api/v1/events", params={"service": "auth-api"}).json()

        assert [e["service"] for e in results] == ["auth-api"]

    def test_filter_by_level_normalizes_input(self, client):
        client.post("/api/v1/events", json=_payload(level="error"))
        client.post("/api/v1/events", json=_payload(level="info"))

        results = client.get("/api/v1/events", params={"level": "warning"}).json()

        assert results == []

    def test_pagination_limit_and_offset(self, client):
        for minute in range(5):
            client.post("/api/v1/events", json=_payload(timestamp=f"2026-06-18T10:0{minute}:00Z"))

        page = client.get("/api/v1/events", params={"limit": 2, "offset": 2}).json()

        assert len(page) == 2
