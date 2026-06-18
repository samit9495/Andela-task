"""Data access for anomalies."""

from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.anomaly import Anomaly


class AnomalyRepository:
    """Persistence and queries for ``Anomaly`` rows."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def add_all(self, anomalies: Sequence[Anomaly]) -> list[Anomaly]:
        self._db.add_all(anomalies)
        return list(anomalies)

    def exists(
        self,
        *,
        service: str,
        signature: str | None,
        strategy: str,
        window_start: datetime,
    ) -> bool:
        signature_clause = (
            Anomaly.signature.is_(None) if signature is None else Anomaly.signature == signature
        )
        stmt = select(Anomaly.id).where(
            Anomaly.service == service,
            signature_clause,
            Anomaly.strategy == strategy,
            Anomaly.window_start == window_start,
        )
        return self._db.execute(stmt).first() is not None
