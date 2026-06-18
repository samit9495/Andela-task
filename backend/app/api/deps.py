"""FastAPI dependency providers for the API layer."""

from fastapi import Depends
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.ingestion.ingestion_service import IngestionService
from backend.app.repositories.event_repository import EventRepository


def get_event_repository(db: Session = Depends(get_db)) -> EventRepository:
    return EventRepository(db)


def get_ingestion_service(db: Session = Depends(get_db)) -> IngestionService:
    return IngestionService(db)
