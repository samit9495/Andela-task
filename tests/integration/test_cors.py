"""CORS is enabled for the configured dashboard origin."""


class TestCors:
    def test_allowed_origin_receives_cors_header(self, client):
        response = client.get("/health", headers={"Origin": "http://localhost:5173"})

        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
