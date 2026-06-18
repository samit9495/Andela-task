"""API throttling: 429 Too Many Requests spikes on the gateway."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime, timedelta
from random import Random

from .base import GeneratedEvent

_SERVICE = "api-gateway"
_BURST_START = 10
_BURST_END = 50


class ThrottlingScenario:
    name = "throttling"

    def generate(
        self, *, start: datetime, duration_seconds: int, rng: Random
    ) -> Iterator[GeneratedEvent]:
        for second in range(duration_seconds):
            ts = start + timedelta(seconds=second)
            if rng.random() < 0.5:
                yield GeneratedEvent(_SERVICE, "INFO", "request handled", ts)
            if _BURST_START <= second <= _BURST_END:
                for _ in range(rng.randint(2, 5)):
                    level = "ERROR" if rng.random() < 0.3 else "WARN"
                    yield GeneratedEvent(_SERVICE, level, "429 Too Many Requests", ts)
