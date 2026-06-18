"""Listing incidents must not N+1 over their anomalies."""

from datetime import UTC, datetime

from backend.app.incidents.incident_service import IncidentService
from backend.app.models.anomaly import Anomaly
from backend.app.repositories.incident_repository import IncidentRepository
from sqlalchemy import event

_NOW = datetime(2026, 6, 18, 10, 0, 0, tzinfo=UTC)


def _anomaly(service: str = "payment-api") -> Anomaly:
    return Anomaly(
        strategy="z_score",
        service=service,
        signature=None,
        score=9.0,
        baseline_value=10.0,
        current_value=70.0,
        window_start=_NOW,
        window_end=_NOW,
    )


def _seed(db, count: int) -> None:
    service_obj = IncidentService(db)
    for index in range(count):
        anomalies = [_anomaly(f"svc-{index}"), _anomaly(f"svc-{index}")]
        db.add_all(anomalies)
        db.commit()
        service_obj.open_incident(f"svc-{index}", anomalies, _NOW)


def _select_count(engine) -> tuple[list[str], callable]:  # type: ignore[type-arg]
    statements: list[str] = []

    def listener(conn, cursor, statement, parameters, context, executemany):
        if statement.lstrip().upper().startswith("SELECT"):
            statements.append(statement)

    event.listen(engine, "after_cursor_execute", listener)

    def remove() -> None:
        event.remove(engine, "after_cursor_execute", listener)

    return statements, remove


class TestIncidentRepositoryEagerLoad:
    def test_list_does_not_N_plus_1_over_anomalies(self, db, engine):
        _seed(db, count=5)
        db.expire_all()

        statements, remove = _select_count(engine)
        try:
            incidents = IncidentRepository(db).list()
            # Touch the relationship to force any lazy load.
            _ = [list(incident.anomalies) for incident in incidents]
        finally:
            remove()

        assert len(incidents) == 5
        anomaly_selects = [s for s in statements if "FROM anomalies" in s]
        # selectinload issues exactly one IN(...) query for the related rows.
        assert len(anomaly_selects) == 1, statements

    def test_list_unresolved_does_not_N_plus_1_over_anomalies(self, db, engine):
        _seed(db, count=5)
        db.expire_all()

        statements, remove = _select_count(engine)
        try:
            incidents = IncidentRepository(db).list_unresolved()
            _ = [list(incident.anomalies) for incident in incidents]
        finally:
            remove()

        assert len(incidents) == 5
        anomaly_selects = [s for s in statements if "FROM anomalies" in s]
        assert len(anomaly_selects) == 1, statements
