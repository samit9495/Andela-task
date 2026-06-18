"""Integration tests for application startup and the health endpoint."""


class TestHealthEndpoint:
    def test_app_starts_and_health_returns_ok(self, client):
        response = client.get("/health")

        assert response.status_code == 200

    def test_health_payload_shape(self, client):
        body = client.get("/health").json()

        assert body["status"] == "ok"
        assert body["version"]
        assert body["ai_mode"] in {"mock", "gemini"}
