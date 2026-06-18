"""Unit tests for PromptLog (persists llm_evaluations + appends docs/llm_prompts.md)."""

from backend.app.models.enums import IncidentCategory
from backend.app.repositories.llm_evaluation_repository import LLMEvaluationRepository
from backend.app.triage.prompt_log import PromptLog
from backend.app.triage.schemas import ClassificationOutput


def _output():
    return ClassificationOutput(category=IncidentCategory.DATABASE, confidence=0.9, reasoning="db")


class TestPromptLog:
    def test_record_persists_row_and_appends_markdown(self, db, tmp_path):
        path = tmp_path / "llm_prompts.md"
        log = PromptLog(db, model="gemini-1.5-flash", log_path=path)

        row = log.record(
            agent="classification",
            prompt_version="classification_v1",
            prompt="hello world",
            response=_output(),
            status="ok",
            latency_ms=12,
            incident_id=5,
        )

        assert row.id is not None
        assert row.status == "ok"
        assert LLMEvaluationRepository(db).list_for_incident(5) == [row]
        content = path.read_text(encoding="utf-8")
        assert "classification" in content
        assert "status=ok" in content
        assert "hello world" in content

    def test_record_failure_logs_empty_response(self, db, tmp_path):
        path = tmp_path / "llm_prompts.md"
        log = PromptLog(db, model="gemini-1.5-flash", log_path=path)

        row = log.record(
            agent="root_cause",
            prompt_version="root_cause_v1",
            prompt="p",
            response=None,
            status="LLMTimeout",
            latency_ms=5,
        )

        assert row.response == ""
        assert "status=LLMTimeout" in path.read_text(encoding="utf-8")

    def test_next_request_id_is_unique(self, db, tmp_path):
        log = PromptLog(db, model="m", log_path=tmp_path / "p.md")

        assert log.next_request_id() != log.next_request_id()
