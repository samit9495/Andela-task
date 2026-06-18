"""Computes the platform risk score (MASTER_PLAN section 26.3).

Risk = 100 - error_penalty - alert_penalty - incident_penalty, clamped [0, 100].
"""

from sqlalchemy.orm import Session

from backend.app.models.enums import LogLevel, Severity
from backend.app.repositories.alert_repository import AlertRepository
from backend.app.repositories.event_repository import EventRepository
from backend.app.repositories.incident_repository import IncidentRepository
from backend.app.schemas.risk import RiskScoreResponse

_SEVERITY_WEIGHTS = {
    Severity.CRITICAL.value: 20.0,
    Severity.HIGH.value: 12.0,
    Severity.MEDIUM.value: 6.0,
    Severity.LOW.value: 2.0,
}

_ERROR_PENALTY_CAP = 40.0
_ALERT_PENALTY_CAP = 30.0
_INCIDENT_PENALTY_CAP = 50.0
_ERROR_PENALTY_FACTOR = 0.8
_ALERT_PENALTY_FACTOR = 5.0
_HEALTHY_BAND = 90.0
_WARNING_BAND = 70.0


def _band(score: float) -> str:
    if score >= _HEALTHY_BAND:
        return "Healthy"
    if score >= _WARNING_BAND:
        return "Warning"
    return "Critical"


class RiskScoreService:
    """Aggregates error rate, alerts, and incidents into a 0-100 risk score."""

    def __init__(self, db: Session) -> None:
        self._event_repo = EventRepository(db)
        self._incident_repo = IncidentRepository(db)
        self._alert_repo = AlertRepository(db)

    def calculate(self) -> RiskScoreResponse:
        total_events = self._event_repo.count()
        by_level = self._event_repo.count_by_level()
        error_events = by_level.get(LogLevel.ERROR.value, 0) + by_level.get(
            LogLevel.CRITICAL.value, 0
        )
        error_rate_pct = (error_events / total_events * 100.0) if total_events else 0.0
        error_penalty = min(_ERROR_PENALTY_CAP, error_rate_pct * _ERROR_PENALTY_FACTOR)

        open_alerts = self._alert_repo.count_distinct_incidents()
        alert_penalty = min(_ALERT_PENALTY_CAP, open_alerts * _ALERT_PENALTY_FACTOR)

        incidents = self._incident_repo.list_unresolved()
        incident_penalty = min(
            _INCIDENT_PENALTY_CAP,
            sum(_SEVERITY_WEIGHTS.get(incident.severity, 0.0) for incident in incidents),
        )

        score = max(0.0, min(100.0, 100.0 - error_penalty - alert_penalty - incident_penalty))
        return RiskScoreResponse(
            score=round(score, 2),
            status=_band(score),
            error_penalty=round(error_penalty, 2),
            alert_penalty=round(alert_penalty, 2),
            incident_penalty=round(incident_penalty, 2),
        )
