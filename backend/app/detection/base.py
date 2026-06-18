"""Detector protocol and the value object detectors return.

Detectors are pure: they take a numeric baseline series and a current value and
return an ``AnomalySignal`` (or ``None``). They know nothing about the database;
the ``DetectionService`` maps signals to persisted ``Anomaly`` rows.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class AnomalySignal:
    """A detected deviation, independent of persistence."""

    strategy: str
    score: float
    baseline_value: float
    current_value: float


class Detector(Protocol):
    """Contract every detection strategy honors (Liskov-substitutable)."""

    strategy: str

    def detect(self, baseline: Sequence[float], current: float) -> AnomalySignal | None: ...
