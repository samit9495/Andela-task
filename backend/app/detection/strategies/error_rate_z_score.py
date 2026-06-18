"""Z-Score error-rate spike detector."""

from collections.abc import Sequence

import numpy as np

from backend.app.detection.base import AnomalySignal


class ZScoreDetector:
    """Flags a current value whose Z-Score exceeds the threshold (upward only)."""

    strategy = "z_score"

    def __init__(self, threshold: float, min_samples: int = 10) -> None:
        self.threshold = threshold
        self.min_samples = min_samples

    def detect(self, baseline: Sequence[float], current: float) -> AnomalySignal | None:
        values = np.asarray(list(baseline), dtype=float)
        if values.size < self.min_samples:
            return None
        mean = float(values.mean())
        std = float(values.std())
        if std == 0.0:
            return None
        z_score = (current - mean) / std
        if z_score >= self.threshold:
            return AnomalySignal(self.strategy, float(z_score), mean, float(current))
        return None
