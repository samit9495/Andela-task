"""Turns stored events into persisted anomalies.

Pulls recent events for a service, buckets their timestamps into a per-minute
count series, runs the rate detectors on the ERROR/CRITICAL series and the
signature-frequency detector per signature, and persists the resulting anomalies
(deduplicated within the current window).
"""

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from backend.app.core.config import Settings, get_settings
from backend.app.detection.base import AnomalySignal, Detector
from backend.app.detection.strategies.error_rate_ewma import EWMADetector
from backend.app.detection.strategies.error_rate_z_score import ZScoreDetector
from backend.app.detection.strategies.signature_frequency import SignatureFrequencyDetector
from backend.app.models.anomaly import Anomaly
from backend.app.models.enums import LogLevel
from backend.app.repositories.anomaly_repository import AnomalyRepository
from backend.app.repositories.event_repository import EventRepository

_ERROR_LEVELS = (LogLevel.ERROR.value, LogLevel.CRITICAL.value)


class DetectionService:
    """Coordinates detectors over a service's recent event history."""

    def __init__(self, db: Session, settings: Settings | None = None) -> None:
        self._db = db
        self._settings = settings or get_settings()
        self._event_repo = EventRepository(db)
        self._anomaly_repo = AnomalyRepository(db)
        config = self._settings
        self._rate_detectors: list[Detector] = [
            ZScoreDetector(
                threshold=config.z_score_threshold,
                min_samples=config.min_baseline_samples,
            ),
            EWMADetector(
                alpha=config.ewma_alpha,
                drift_threshold=config.ewma_drift_threshold,
                min_samples=config.min_baseline_samples,
            ),
        ]
        self._signature_detector = SignatureFrequencyDetector(
            multiplier=config.signature_burst_multiplier,
            floor=config.signature_burst_floor,
        )

    def analyze_service(self, service: str, now: datetime) -> list[Anomaly]:
        config = self._settings
        num_buckets = config.min_baseline_samples + 1
        bucket_seconds = config.detection_bucket_seconds
        since = now - timedelta(seconds=num_buckets * bucket_seconds)
        events = self._event_repo.list(service=service, since=since, limit=100_000)

        window_start = now - timedelta(seconds=bucket_seconds)
        window_end = now
        detected: list[Anomaly] = []

        error_timestamps = [e.timestamp for e in events if e.level in _ERROR_LEVELS]
        rate_series = self._bucketize(error_timestamps, now, bucket_seconds, num_buckets)
        for detector in self._rate_detectors:
            signal = detector.detect(rate_series[:-1], float(rate_series[-1]))
            if signal and not self._is_duplicate(service, None, detector.strategy, window_start):
                detected.append(self._to_anomaly(service, None, signal, window_start, window_end))

        for signature in sorted({e.signature for e in events if e.signature is not None}):
            sig_timestamps = [e.timestamp for e in events if e.signature == signature]
            series = self._bucketize(sig_timestamps, now, bucket_seconds, num_buckets)
            signal = self._signature_detector.detect(series[:-1], float(series[-1]))
            if signal and not self._is_duplicate(
                service, signature, self._signature_detector.strategy, window_start
            ):
                detected.append(
                    self._to_anomaly(service, signature, signal, window_start, window_end)
                )

        if detected:
            self._anomaly_repo.add_all(detected)
            self._db.commit()
            for anomaly in detected:
                self._db.refresh(anomaly)
        return detected

    def _is_duplicate(
        self, service: str, signature: str | None, strategy: str, window_start: datetime
    ) -> bool:
        return self._anomaly_repo.exists(
            service=service, signature=signature, strategy=strategy, window_start=window_start
        )

    @staticmethod
    def _bucketize(
        timestamps: Sequence[datetime], now: datetime, bucket_seconds: int, num_buckets: int
    ) -> list[int]:
        buckets = [0] * num_buckets
        for raw in timestamps:
            timestamp = raw if raw.tzinfo is not None else raw.replace(tzinfo=UTC)
            delta = (now - timestamp).total_seconds()
            if delta < 0:
                index = num_buckets - 1
            else:
                from_end = int(delta // bucket_seconds)
                if from_end >= num_buckets:
                    continue
                index = num_buckets - 1 - from_end
            buckets[index] += 1
        return buckets

    @staticmethod
    def _to_anomaly(
        service: str,
        signature: str | None,
        signal: AnomalySignal,
        window_start: datetime,
        window_end: datetime,
    ) -> Anomaly:
        return Anomaly(
            strategy=signal.strategy,
            service=service,
            signature=signature,
            score=signal.score,
            baseline_value=signal.baseline_value,
            current_value=signal.current_value,
            window_start=window_start,
            window_end=window_end,
        )
