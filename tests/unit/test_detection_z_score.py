"""Unit tests for the Z-Score error-rate detector."""

from backend.app.detection.strategies.error_rate_z_score import ZScoreDetector

_BASELINE = [10, 11, 9, 12, 10, 11, 10, 9, 11, 10]


class TestZScoreDetector:
    def test_flags_anomaly_when_rate_exceeds_threshold(self):
        detector = ZScoreDetector(threshold=3.0, min_samples=10)

        signal = detector.detect(_BASELINE, 70)

        assert signal is not None
        assert signal.strategy == "z_score"
        assert signal.current_value == 70

    def test_returns_none_within_threshold(self):
        detector = ZScoreDetector(threshold=3.0, min_samples=10)

        assert detector.detect(_BASELINE, 12) is None

    def test_returns_none_with_insufficient_baseline(self):
        detector = ZScoreDetector(threshold=3.0, min_samples=10)

        assert detector.detect([10, 11, 9], 70) is None

    def test_returns_none_with_zero_variance(self):
        detector = ZScoreDetector(threshold=3.0, min_samples=3)

        assert detector.detect([10, 10, 10], 70) is None

    def test_does_not_flag_drops(self):
        detector = ZScoreDetector(threshold=3.0, min_samples=10)

        assert detector.detect(_BASELINE, 0) is None
