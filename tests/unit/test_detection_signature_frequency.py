"""Unit tests for the signature-frequency detector."""

from backend.app.detection.strategies.signature_frequency import SignatureFrequencyDetector


class TestSignatureFrequencyDetector:
    def test_flags_burst_over_multiplier(self):
        detector = SignatureFrequencyDetector(multiplier=5.0, floor=10)

        signal = detector.detect([2, 2, 2, 2], 70)

        assert signal is not None
        assert signal.strategy == "signature_frequency"

    def test_respects_floor_for_low_baseline(self):
        detector = SignatureFrequencyDetector(multiplier=5.0, floor=10)

        # 3 is 5x above a ~0.3 baseline, but below the absolute floor of 10.
        assert detector.detect([0, 0, 1], 3) is None

    def test_flags_when_exceeds_floor_with_zero_baseline(self):
        detector = SignatureFrequencyDetector(multiplier=5.0, floor=10)

        assert detector.detect([0, 0], 15) is not None

    def test_returns_none_when_below_threshold(self):
        detector = SignatureFrequencyDetector(multiplier=5.0, floor=10)

        assert detector.detect([10, 10], 12) is None
