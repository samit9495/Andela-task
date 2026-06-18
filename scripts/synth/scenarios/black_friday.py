"""Black Friday: a large overall volume increase, mostly INFO but more errors."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime, timedelta
from random import Random

from .base import GeneratedEvent

_SERVICES = ["api-gateway", "payment-api", "auth-service", "orders-api", "checkout-service"]


class BlackFridayScenario:
    name = "black_friday"

    def generate(
        self, *, start: datetime, duration_seconds: int, rng: Random
    ) -> Iterator[GeneratedEvent]:
        for second in range(duration_seconds):
            ts = start + timedelta(seconds=second)
            for _ in range(rng.randint(8, 15)):
                service = rng.choice(_SERVICES)
                yield GeneratedEvent(service, "INFO", "request handled", ts)
            for _ in range(rng.randint(0, 3)):
                service = rng.choice(_SERVICES)
                level = "CRITICAL" if rng.random() < 0.1 else "ERROR"
                yield GeneratedEvent(service, level, "request failed under load", ts)
