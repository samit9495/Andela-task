"""Memory leak: a slow rise in WARN/ERROR over a long window on one service."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime, timedelta
from random import Random

from .base import GeneratedEvent

_SERVICE = "orders-api"


class MemoryLeakScenario:
    name = "memory_leak"

    def generate(
        self, *, start: datetime, duration_seconds: int, rng: Random
    ) -> Iterator[GeneratedEvent]:
        for second in range(duration_seconds):
            ts = start + timedelta(seconds=second)
            progress = second / max(duration_seconds - 1, 1)
            yield GeneratedEvent(_SERVICE, "INFO", "request handled", ts)
            if rng.random() < 0.2 + 0.5 * progress:
                if progress > 0.8 and rng.random() < 0.3:
                    yield GeneratedEvent(_SERVICE, "CRITICAL", "OutOfMemoryError", ts)
                else:
                    level = "ERROR" if progress > 0.5 else "WARN"
                    yield GeneratedEvent(_SERVICE, level, "Heap memory usage above threshold", ts)
