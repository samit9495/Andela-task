"""Shared types for synthetic traffic scenarios.

Scenarios are pure and deterministic: they take an injected ``random.Random``
and never touch the network, the clock, or the backend.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime
from random import Random
from typing import Any, Protocol


@dataclass(frozen=True)
class GeneratedEvent:
    service: str
    level: str
    message: str
    timestamp: datetime
    metadata: dict[str, Any] | None = field(default=None)


class Scenario(Protocol):
    name: str

    def generate(
        self, *, start: datetime, duration_seconds: int, rng: Random
    ) -> Iterable[GeneratedEvent]:
        """Yield the events that make up this scenario."""
        ...
