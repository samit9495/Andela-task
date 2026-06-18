"""Authentication failures: a burst of 401 / JWT errors on the auth service."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime, timedelta
from random import Random

from .base import GeneratedEvent

_SERVICE = "auth-service"
_MESSAGES = [
    "401 Unauthorized",
    "JWT verification failed",
    "JWT token expired",
    "401 invalid credentials",
]
_BURST_START = 5
_BURST_END = 45


class AuthFailuresScenario:
    name = "auth_failures"

    def generate(
        self, *, start: datetime, duration_seconds: int, rng: Random
    ) -> Iterator[GeneratedEvent]:
        for second in range(duration_seconds):
            ts = start + timedelta(seconds=second)
            if rng.random() < 0.4:
                yield GeneratedEvent(_SERVICE, "INFO", "login succeeded", ts)
            if _BURST_START <= second <= _BURST_END:
                for _ in range(rng.randint(2, 5)):
                    yield GeneratedEvent(_SERVICE, "ERROR", rng.choice(_MESSAGES), ts)
