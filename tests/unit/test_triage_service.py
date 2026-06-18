"""Unit tests for the TriageService orchestration."""

from datetime import UTC, datetime

from backend.app.core.exceptions import LLMTimeout
from backend.app.models.anomaly import Anomaly
from backend.app.models.enums import IncidentCategory
from backend.app.models.incident import Incident
from backend.app.rag.embedder import HashingEmbedder
from backend.app.rag.retriever import RunbookRetriever
from backend.app.rag.runbook_loader import RunbookLoader
from backend.app.repositories.llm_evaluation_repository import LLMEvaluationRepository
from backend.app.triage.llm_client import FakeLLMClient
from backend.app.triage.schemas import (
    ClassificationOutput,
    ExecutiveSummaryOutput,
    RemediationActions,
    RootCauseAnalysis,
)
from backend.app.triage.triage_service import TriageService


def _retriever() -> RunbookRetriever:
    runbooks = RunbookLoader("data/runbooks").load_all()
    return RunbookRetriever(HashingEmbedder(), runbooks, top_k=3, min_similarity=0.0)


def _incident(db) -> Incident:
    now = datetime.now(tz=UTC)
    incident = Incident(title="DB timeouts", service="payment-api", severity="HIGH", status="OPEN")
    incident.anomalies = [
        Anomaly(
            strategy="signature_frequency",
            service="payment-api",
            signature="Database timeout",
            score=9.0,
            baseline_value=2.0,
            current_value=70.0,
            window_start=now,
            window_end=now,
        )
    ]
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident


def _fake_with_all_outputs() -> FakeLLMClient:
    fake = FakeLLMClient()
    fake.register_for_schema(
        ClassificationOutput,
        ClassificationOutput(category=IncidentCategory.DATABASE, confidence=0.9, reasoning="db"),
    )
    fake.register_for_schema(
        RootCauseAnalysis,
        RootCauseAnalysis(root_cause="connection pool exhausted", confidence=0.8),
    )
    fake.register_for_schema(
        RemediationActions, RemediationActions(recommended_actions=["Increase pool size"])
    )
    fake.register_for_schema(
        ExecutiveSummaryOutput,
        ExecutiveSummaryOutput(executive_summary="Database incident triaged."),
    )
    return fake


class TestTriageService:
    def test_triage_produces_report_updates_incident_and_logs(self, db, tmp_path):
        incident = _incident(db)
        service = TriageService(
            db, _fake_with_all_outputs(), _retriever(), model="test", log_path=tmp_path / "p.md"
        )

        report = service.triage(incident)

        assert report.category == IncidentCategory.DATABASE
        assert report.root_cause == "connection pool exhausted"
        assert report.recommended_actions == ["Increase pool size"]
        assert any(ref.slug == "database_timeout" for ref in report.references)
        assert report.executive_summary == "Database incident triaged."

        db.refresh(incident)
        assert incident.category == "database"
        assert incident.root_cause == "connection pool exhausted"
        assert incident.summary == "Database incident triaged."
        assert incident.confidence_score is not None

        rows = LLMEvaluationRepository(db).list_for_incident(incident.id)
        assert len(rows) == 4

    def test_triage_falls_back_when_llm_fails(self, db, tmp_path):
        incident = _incident(db)
        fake = FakeLLMClient()
        fake.set_to_raise(LLMTimeout("slow"))
        service = TriageService(db, fake, _retriever(), model="test", log_path=tmp_path / "p.md")

        report = service.triage(incident)

        assert report.category == IncidentCategory.UNKNOWN
        assert report.recommended_actions
        assert any(ref.slug == "database_timeout" for ref in report.references)
        assert len(LLMEvaluationRepository(db).list_for_incident(incident.id)) == 4
