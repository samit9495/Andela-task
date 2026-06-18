"""Integration-style unit tests for the end-to-end PipelineService.

Seeds an error storm, then asserts the pipeline detects, correlates, triages
(via the offline MockAIClient), and raises alerts.
"""

from datetime import UTC, datetime, timedelta

from backend.app.core.config import Settings
from backend.app.models.enums import IncidentStatus
from backend.app.models.event import Event
from backend.app.pipeline.pipeline_service import PipelineService
from backend.app.rag.embedder import HashingEmbedder
from backend.app.rag.retriever import RunbookRetriever
from backend.app.repositories.alert_repository import AlertRepository
from backend.app.triage.mock_ai_client import MockAIClient

_NOW = datetime(2026, 6, 18, 10, 0, 0, tzinfo=UTC)


def _settings(tmp_path):
    return Settings(
        _env_file=None,
        min_baseline_samples=3,
        detection_bucket_seconds=60,
        signature_burst_floor=5,
        signature_burst_multiplier=5.0,
        llm_prompt_log_path=str(tmp_path / "llm_prompts.md"),
    )


def _retriever() -> RunbookRetriever:
    return RunbookRetriever(HashingEmbedder(), [])


def _seed_spike(db):
    events = [_event(_NOW - timedelta(seconds=minute * 60 + 1)) for minute in (1, 2, 3)]
    events += [_event(_NOW - timedelta(seconds=1)) for _ in range(20)]
    db.add_all(events)
    db.commit()


def _event(ts):
    return Event(
        service="payment-api",
        level="ERROR",
        message="Database timeout",
        signature="Database timeout",
        timestamp=ts,
    )


def _pipeline(db, tmp_path) -> PipelineService:
    return PipelineService(db, MockAIClient(), _retriever(), settings=_settings(tmp_path))


class TestPipelineService:
    def test_quiet_service_produces_no_incident(self, db, tmp_path):
        db.add(_event(_NOW - timedelta(seconds=1)))
        db.commit()

        assert _pipeline(db, tmp_path).process_service("payment-api", _NOW) is None

    def test_storm_creates_triaged_incident_with_alerts(self, db, tmp_path):
        _seed_spike(db)

        incident = _pipeline(db, tmp_path).process_service("payment-api", _NOW)

        assert incident is not None
        assert incident.status == IncidentStatus.OPEN.value
        assert incident.category is not None
        assert incident.summary is not None
        assert AlertRepository(db).count_distinct_incidents() == 1

    def test_process_services_aggregates_only_real_incidents(self, db, tmp_path):
        _seed_spike(db)

        incidents = _pipeline(db, tmp_path).process_services(["payment-api", "quiet-service"], _NOW)

        assert [i.service for i in incidents] == ["payment-api"]

    def test_rerun_does_not_retriage_or_realert(self, db, tmp_path):
        _seed_spike(db)
        pipeline = _pipeline(db, tmp_path)
        incident = pipeline.process_service("payment-api", _NOW)
        assert incident is not None
        first_summary = incident.summary

        again = pipeline.process_service("payment-api", _NOW)

        assert again is None
        assert incident.summary == first_summary
