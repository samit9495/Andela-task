"""Unit tests for the request body-size limit middleware."""

from backend.app.api.middleware import BodySizeLimitMiddleware
from fastapi import FastAPI
from fastapi.testclient import TestClient


def _app(max_bytes: int) -> FastAPI:
    app = FastAPI()
    app.add_middleware(BodySizeLimitMiddleware, max_bytes=max_bytes)

    @app.post("/echo")
    async def echo(payload: dict) -> dict:
        return payload

    return app


class TestBodySizeLimitMiddleware:
    def test_rejects_payload_over_limit_with_413(self):
        client = TestClient(_app(max_bytes=10))

        response = client.post("/echo", json={"message": "x" * 100})

        assert response.status_code == 413
        body = response.json()
        assert body["code"] == "payload_too_large"
        assert "detail" in body

    def test_allows_payload_under_limit(self):
        client = TestClient(_app(max_bytes=10_000))

        response = client.post("/echo", json={"ok": True})

        assert response.status_code == 200
        assert response.json() == {"ok": True}
