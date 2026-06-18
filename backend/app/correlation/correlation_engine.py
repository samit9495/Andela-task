"""Groups anomalies into incidents within a correlation window.

Within ``correlation_window_seconds`` an open incident for the same service
absorbs new anomalies; otherwise a new incident is opened.
"""

from collections.abc import Sequence
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from backend.app.core.config import Settings, get_settings
from backend.app.incidents.incident_service import IncidentService
from backend.app.models.anomaly import Anomaly
from backend.app.models.incident import Incident
from backend.app.repositories.incident_repository import IncidentRepository


class CorrelationEngine:
    """Correlates anomalies of one service into a single incident."""

    def __init__(self, db: Session, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._incident_repo = IncidentRepository(db)
        self._incident_service = IncidentService(db)

    def correlate(
        self, service: str, anomalies: Sequence[Anomaly], now: datetime
    ) -> Incident | None:
        if not anomalies:
            return None
        since = now - timedelta(seconds=self._settings.correlation_window_seconds)
        incident = self._incident_repo.find_open_for_service(service, since)
        if incident is None:
            return self._incident_service.open_incident(service, anomalies, now)
        return self._incident_service.attach_anomalies(incident, anomalies, now)
