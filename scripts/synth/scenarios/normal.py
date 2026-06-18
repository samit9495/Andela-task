"""Normal traffic: mostly INFO with sparse WARN and the occasional ERROR."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime, timedelta
from random import Random

from .base import GeneratedEvent

_SERVICES = ["api-gateway", "payment-api", "auth-service", "orders-api"]


class NormalScenario:
    name = "normal"

    def generate(
        self, *, start: datetime, duration_seconds: int, rng: Random
    ) -> Iterator[GeneratedEvent]:
        for second in range(duration_seconds):
            ts = start + timedelta(seconds=second)
            for service in _SERVICES:
                roll = rng.random()
                if roll < 0.70:
                    yield GeneratedEvent(service, "INFO", "request handled", ts)
                elif roll < 0.75:
                    yield GeneratedEvent(service, "WARN", "elevated latency", ts)
                elif roll < 0.76:
                    yield GeneratedEvent(service, "ERROR", "unhandled exception", ts)
