"""End-to-end pipeline: detect -> correlate -> triage -> alert.

Invoked per affected service after ingestion. Triage runs once per incident
(only while it is still untriaged) and alerts are deduplicated by AlertService.
"""

from collections.abc import Iterable
from datetime import datetime

from sqlalchemy.orm import Session

from backend.app.alerts.alert_service import AlertService
from backend.app.core.config import Settings, get_settings
from backend.app.correlation.correlation_engine import CorrelationEngine
from backend.app.detection.detection_service import DetectionService
from backend.app.models.incident import Incident
from backend.app.rag.retriever import RunbookRetriever
from backend.app.triage.llm_client import LLMClient
from backend.app.triage.triage_service import TriageService


class PipelineService:
    """Runs the full observability pipeline for one service at a time."""

    def __init__(
        self,
        db: Session,
        llm: LLMClient,
        retriever: RunbookRetriever,
        settings: Settings | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._detection = DetectionService(db, self._settings)
        self._correlation = CorrelationEngine(db, self._settings)
        self._triage = TriageService(
            db,
            llm,
            retriever,
            model=self._settings.model_name,
            log_path=self._settings.llm_prompt_log_path,
        )
        self._alerts = AlertService(db)

    def process_service(self, service: str, now: datetime) -> Incident | None:
        anomalies = self._detection.analyze_service(service, now)
        if not anomalies:
            return None
        incident = self._correlation.correlate(service, anomalies, now)
        if incident is None:
            return None
        if incident.category is None:
            self._triage.triage(incident)
        self._alerts.raise_for_incident(incident, now)
        return incident

    def process_services(self, services: Iterable[str], now: datetime) -> list[Incident]:
        incidents: list[Incident] = []
        for service in dict.fromkeys(services):
            incident = self.process_service(service, now)
            if incident is not None:
                incidents.append(incident)
        return incidents
