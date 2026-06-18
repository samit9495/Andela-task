"""FastAPI dependency providers for the API layer."""

from functools import lru_cache

from fastapi import Depends
from sqlalchemy.orm import Session

from backend.app.core.config import Settings, get_settings
from backend.app.db.session import get_db
from backend.app.incidents.incident_service import IncidentService
from backend.app.ingestion.ingestion_service import IngestionService
from backend.app.pipeline.pipeline_service import PipelineService
from backend.app.rag.retriever import RunbookRetriever, build_runbook_retriever
from backend.app.repositories.alert_repository import AlertRepository
from backend.app.repositories.event_repository import EventRepository
from backend.app.repositories.topology_repository import ServiceTopologyRepository
from backend.app.risk.risk_score_service import RiskScoreService
from backend.app.topology.topology_engine import TopologyEngine
from backend.app.triage.gemini_client import GeminiLLMClient
from backend.app.triage.llm_client import LLMClient
from backend.app.triage.mock_ai_client import MockAIClient


def get_event_repository(db: Session = Depends(get_db)) -> EventRepository:
    return EventRepository(db)


def get_ingestion_service(db: Session = Depends(get_db)) -> IngestionService:
    return IngestionService(db)


def get_incident_service(db: Session = Depends(get_db)) -> IncidentService:
    return IncidentService(db)


def get_risk_score_service(db: Session = Depends(get_db)) -> RiskScoreService:
    return RiskScoreService(db)


def get_alert_repository(db: Session = Depends(get_db)) -> AlertRepository:
    return AlertRepository(db)


@lru_cache
def _build_llm_client() -> LLMClient:
    settings = get_settings()
    if settings.ai_mode == "gemini":
        return GeminiLLMClient(api_key=settings.gemini_api_key, model=settings.model_name)
    return MockAIClient()


def get_llm_client() -> LLMClient:
    return _build_llm_client()


@lru_cache
def _build_retriever() -> RunbookRetriever:
    return build_runbook_retriever()


def get_retriever() -> RunbookRetriever:
    return _build_retriever()


def get_pipeline_service(
    db: Session = Depends(get_db),
    llm: LLMClient = Depends(get_llm_client),
    retriever: RunbookRetriever = Depends(get_retriever),
    settings: Settings = Depends(get_settings),
) -> PipelineService:
    return PipelineService(db, llm, retriever, settings=settings)


def get_topology_engine(db: Session = Depends(get_db)) -> TopologyEngine:
    return TopologyEngine(ServiceTopologyRepository(db).adjacency())
