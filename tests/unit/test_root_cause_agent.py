"""Unit tests for the Root Cause Agent."""

from backend.app.core.exceptions import LLMTimeout
from backend.app.models.enums import IncidentCategory
from backend.app.triage.agents.root_cause_agent import RootCauseAgent
from backend.app.triage.llm_client import FakeLLMClient
from backend.app.triage.prompt_log import NullPromptLog
from backend.app.triage.schemas import RootCauseAnalysis


class TestRootCauseAgent:
    def test_returns_llm_root_cause(self):
        fake = FakeLLMClient()
        fake.register_for_schema(
            RootCauseAnalysis,
            RootCauseAnalysis(root_cause="connection pool exhausted", confidence=0.8),
        )
        agent = RootCauseAgent(fake, NullPromptLog())

        out = agent.analyze(
            incident_summary="db timeouts",
            category=IncidentCategory.DATABASE,
            top_events=[("Database timeout", 70, "ERROR")],
        )

        assert "pool" in out.root_cause
        assert out.confidence == 0.8

    def test_falls_back_on_failure(self):
        fake = FakeLLMClient()
        fake.set_to_raise(LLMTimeout("slow"))
        agent = RootCauseAgent(fake, NullPromptLog())

        out = agent.analyze(incident_summary="x", category=IncidentCategory.UNKNOWN, top_events=[])

        assert out.confidence == 0.0
        assert out.root_cause
