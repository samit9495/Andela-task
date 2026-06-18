"""Signature-frequency burst detector."""

from collections.abc import Sequence

import numpy as np

from backend.app.detection.base import AnomalySignal


class SignatureFrequencyDetector:
    """Flags a signature whose current count bursts above its baseline.

    Triggers when ``current >= max(multiplier * baseline_mean, floor)``. The
    absolute floor suppresses noise from very low-frequency signatures.
    """

    strategy = "signature_frequency"

    def __init__(self, multiplier: float, floor: int) -> None:
        self.multiplier = multiplier
        self.floor = floor

    def detect(self, baseline: Sequence[float], current: float) -> AnomalySignal | None:
        values = np.asarray(list(baseline), dtype=float)
        baseline_mean = float(values.mean()) if values.size else 0.0
        threshold = max(self.multiplier * baseline_mean, float(self.floor))
        if current >= threshold:
            score = current / baseline_mean if baseline_mean > 0 else float(current)
            return AnomalySignal(self.strategy, float(score), baseline_mean, float(current))
        return None
