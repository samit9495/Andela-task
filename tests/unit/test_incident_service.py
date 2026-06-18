"""Unit tests for IncidentService (creation, absorption, severity, lifecycle)."""

from datetime import UTC, datetime

import pytest
from backend.app.core.exceptions import IncidentNotFound
from backend.app.incidents.incident_service import IncidentService
from backend.app.models.anomaly import Anomaly
from backend.app.models.enums import IncidentStatus, Severity

_NOW = datetime(2026, 6, 18, 10, 0, 0, tzinfo=UTC)


def _anomaly(service="payment-api", strategy="z_score"):
    return Anomaly(
        strategy=strategy,
        service=service,
        signature=None,
        score=9.0,
        baseline_value=10.0,
        current_value=70.0,
        window_start=_NOW,
        window_end=_NOW,
    )


def _persist(db, anomalies):
    db.add_all(anomalies)
    db.commit()
    return anomalies


class TestIncidentService:
    def test_open_incident_links_anomalies_and_sets_severity(self, db):
        service = IncidentService(db)
        anomalies = _persist(db, [_anomaly(), _anomaly()])

        incident = service.open_incident("payment-api", anomalies, _NOW)

        assert incident.id is not None
        assert incident.status == IncidentStatus.OPEN.value
        assert incident.severity == Severity.MEDIUM.value
        assert all(a.incident_id == incident.id for a in anomalies)

    def test_attach_anomalies_raises_severity(self, db):
        service = IncidentService(db)
        first_pair = _persist(db, [_anomaly(), _anomaly()])
        incident = service.open_incident("payment-api", first_pair, _NOW)

        service.attach_anomalies(incident, _persist(db, [_anomaly(), _anomaly()]), _NOW)

        assert incident.severity == Severity.CRITICAL.value
        assert len(incident.anomalies) == 4

    def test_get_unknown_raises(self, db):
        with pytest.raises(IncidentNotFound):
            IncidentService(db).get(999)

    def test_list_filters_by_status(self, db):
        service = IncidentService(db)
        service.open_incident("payment-api", _persist(db, [_anomaly()]), _NOW)

        assert len(service.list(status=IncidentStatus.OPEN.value)) == 1
        assert service.list(status=IncidentStatus.RESOLVED.value) == []

    def test_update_status_to_resolved_sets_resolved_at(self, db):
        service = IncidentService(db)
        incident = service.open_incident("payment-api", _persist(db, [_anomaly()]), _NOW)

        resolved = service.update_status(incident.id, IncidentStatus.RESOLVED, _NOW)

        assert resolved.status == IncidentStatus.RESOLVED.value
        assert resolved.resolved_at is not None
