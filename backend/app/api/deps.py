"""FastAPI dependency providers for the API layer."""

from fastapi import Depends
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.incidents.incident_service import IncidentService
from backend.app.ingestion.ingestion_service import IngestionService
from backend.app.repositories.event_repository import EventRepository
from backend.app.risk.risk_score_service import RiskScoreService


def get_event_repository(db: Session = Depends(get_db)) -> EventRepository:
    return EventRepository(db)


def get_ingestion_service(db: Session = Depends(get_db)) -> IngestionService:
    return IngestionService(db)


def get_incident_service(db: Session = Depends(get_db)) -> IncidentService:
    return IncidentService(db)


def get_risk_score_service(db: Session = Depends(get_db)) -> RiskScoreService:
    return RiskScoreService(db)
