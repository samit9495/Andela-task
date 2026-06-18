"""Incident lifecycle use cases: open, absorb anomalies, query, transition state."""

from collections.abc import Sequence
from datetime import datetime

from sqlalchemy.orm import Session

from backend.app.core.exceptions import IncidentNotFound
from backend.app.models.anomaly import Anomaly
from backend.app.models.enums import IncidentStatus, Severity
from backend.app.models.incident import Incident
from backend.app.repositories.incident_repository import IncidentRepository


def derive_severity(anomaly_count: int) -> Severity:
    """Map the number of correlated anomalies to a severity (documented heuristic)."""
    if anomaly_count >= 4:
        return Severity.CRITICAL
    if anomaly_count == 3:
        return Severity.HIGH
    if anomaly_count == 2:
        return Severity.MEDIUM
    return Severity.LOW


class IncidentService:
    """Create and manage incidents."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._repo = IncidentRepository(db)

    def open_incident(self, service: str, anomalies: Sequence[Anomaly], now: datetime) -> Incident:
        incident = Incident(
            title=f"Degradation in {service}",
            service=service,
            severity=derive_severity(len(anomalies)).value,
            status=IncidentStatus.OPEN.value,
            created_at=now,
            updated_at=now,
        )
        self._repo.add(incident)
        self._db.flush()
        self._link(incident, anomalies)
        self._db.commit()
        self._db.refresh(incident)
        return incident

    def attach_anomalies(
        self, incident: Incident, anomalies: Sequence[Anomaly], now: datetime
    ) -> Incident:
        self._link(incident, anomalies)
        self._db.flush()
        incident.severity = derive_severity(len(incident.anomalies)).value
        incident.updated_at = now
        self._db.commit()
        self._db.refresh(incident)
        return incident

    def get(self, incident_id: int) -> Incident:
        incident = self._repo.get(incident_id)
        if incident is None:
            raise IncidentNotFound(f"incident {incident_id} not found")
        return incident

    def list(self, *, status: str | None = None, severity: str | None = None) -> list[Incident]:
        return self._repo.list(status=status, severity=severity)

    def update_status(self, incident_id: int, status: IncidentStatus, now: datetime) -> Incident:
        incident = self.get(incident_id)
        incident.status = status.value
        incident.updated_at = now
        if status is IncidentStatus.RESOLVED:
            incident.resolved_at = now
        self._db.commit()
        self._db.refresh(incident)
        return incident

    def _link(self, incident: Incident, anomalies: Sequence[Anomaly]) -> None:
        for anomaly in anomalies:
            anomaly.incident_id = incident.id
