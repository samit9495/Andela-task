"""Unit tests for the EWMA error-rate detector."""

from backend.app.detection.strategies.error_rate_ewma import EWMADetector

_BASELINE = [10, 11, 9, 12, 10, 11, 10, 9, 11, 10]


class TestEWMADetector:
    def test_flags_drift_when_current_far_above_ewma(self):
        detector = EWMADetector(alpha=0.3, drift_threshold=3.0, min_samples=10)

        signal = detector.detect(_BASELINE, 80)

        assert signal is not None
        assert signal.strategy == "ewma"

    def test_returns_none_when_stable(self):
        detector = EWMADetector(alpha=0.3, drift_threshold=3.0, min_samples=10)

        assert detector.detect(_BASELINE, 11) is None

    def test_returns_none_with_insufficient_baseline(self):
        detector = EWMADetector(alpha=0.3, drift_threshold=3.0, min_samples=10)

        assert detector.detect([10, 11], 80) is None

    def test_returns_none_with_zero_variance(self):
        detector = EWMADetector(alpha=0.3, drift_threshold=3.0, min_samples=3)

        assert detector.detect([10, 10, 10], 80) is None
