"""EWMA error-rate drift detector."""

from collections.abc import Sequence

import numpy as np

from backend.app.detection.base import AnomalySignal


class EWMADetector:
    """Flags drift of the current value from the exponentially weighted mean."""

    strategy = "ewma"

    def __init__(self, alpha: float, drift_threshold: float, min_samples: int = 10) -> None:
        self.alpha = alpha
        self.drift_threshold = drift_threshold
        self.min_samples = min_samples

    def detect(self, baseline: Sequence[float], current: float) -> AnomalySignal | None:
        values = np.asarray(list(baseline), dtype=float)
        if values.size < self.min_samples:
            return None
        std = float(values.std())
        if std == 0.0:
            return None
        ewma = float(values[0])
        for value in values[1:]:
            ewma = self.alpha * float(value) + (1.0 - self.alpha) * ewma
        score = (current - ewma) / std
        if score >= self.drift_threshold:
            return AnomalySignal(self.strategy, float(score), ewma, float(current))
        return None
