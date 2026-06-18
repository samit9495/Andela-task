"""Integration tests for the metrics API."""


def _payload(service="payment-api", level="error"):
    return {
        "service": service,
        "level": level,
        "message": "Database timeout",
        "timestamp": "2026-06-18T10:00:00Z",
    }


class TestMetrics:
    def test_metrics_empty(self, client):
        body = client.get("/metrics").json()

        assert body == {
            "total_events": 0,
            "events_by_level": {},
            "monitored_services": 0,
            "total_incidents": 0,
            "total_alerts": 0,
            "risk_score": 100.0,
        }

    def test_metrics_counts_events_levels_and_services(self, client):
        client.post("/api/v1/events", json=_payload(service="payment-api", level="error"))
        client.post("/api/v1/events", json=_payload(service="payment-api", level="error"))
        client.post("/api/v1/events", json=_payload(service="auth-api", level="info"))

        body = client.get("/metrics").json()

        assert body["total_events"] == 3
        assert body["events_by_level"] == {"ERROR": 2, "INFO": 1}
        assert body["monitored_services"] == 2
