"""Data access for LLM evaluation audit rows."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.llm_evaluation import LLMEvaluation


class LLMEvaluationRepository:
    """Persistence and queries for ``LLMEvaluation`` rows."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def add(self, evaluation: LLMEvaluation) -> LLMEvaluation:
        self._db.add(evaluation)
        return evaluation

    def list_for_incident(self, incident_id: int) -> list[LLMEvaluation]:
        stmt = (
            select(LLMEvaluation)
            .where(LLMEvaluation.incident_id == incident_id)
            .order_by(LLMEvaluation.id)
        )
        return list(self._db.execute(stmt).scalars().all())
