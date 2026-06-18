"""Database outage: a burst of DB timeout/connection errors across DB consumers."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime, timedelta
from random import Random

from .base import GeneratedEvent

_SERVICES = ["payment-api", "orders-api", "auth-service"]
_MESSAGES = [
    "Database timeout after 20 seconds",
    "Database connection refused",
    "Database connection pool exhausted",
]
_BURST_START = 10
_BURST_END = 50


class DatabaseOutageScenario:
    name = "db_outage"

    def generate(
        self, *, start: datetime, duration_seconds: int, rng: Random
    ) -> Iterator[GeneratedEvent]:
        for second in range(duration_seconds):
            ts = start + timedelta(seconds=second)
            for service in _SERVICES:
                if rng.random() < 0.3:
                    yield GeneratedEvent(service, "INFO", "request handled", ts)
            if _BURST_START <= second <= _BURST_END:
                for _ in range(rng.randint(3, 6)):
                    service = rng.choice(_SERVICES)
                    level = "CRITICAL" if rng.random() < 0.25 else "ERROR"
                    yield GeneratedEvent(service, level, rng.choice(_MESSAGES), ts)
