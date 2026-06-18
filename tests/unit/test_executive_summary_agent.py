"""Unit tests for the Executive Summary Agent."""

from backend.app.core.exceptions import LLMResponseInvalid
from backend.app.models.enums import IncidentCategory
from backend.app.triage.agents.executive_summary_agent import ExecutiveSummaryAgent
from backend.app.triage.llm_client import FakeLLMClient
from backend.app.triage.prompt_log import NullPromptLog
from backend.app.triage.schemas import ExecutiveSummaryOutput


class TestExecutiveSummaryAgent:
    def test_returns_llm_summary(self):
        fake = FakeLLMClient()
        fake.register_for_schema(
            ExecutiveSummaryOutput,
            ExecutiveSummaryOutput(executive_summary="Database incident resolved."),
        )
        agent = ExecutiveSummaryAgent(fake, NullPromptLog())

        out = agent.summarize(
            incident_summary="db",
            category=IncidentCategory.DATABASE,
            root_cause="pool exhausted",
            recommended_actions=["increase pool"],
        )

        assert out.executive_summary == "Database incident resolved."

    def test_falls_back_on_failure(self):
        fake = FakeLLMClient()
        fake.set_to_raise(LLMResponseInvalid("bad"))
        agent = ExecutiveSummaryAgent(fake, NullPromptLog())

        out = agent.summarize(
            incident_summary="db",
            category=IncidentCategory.DATABASE,
            root_cause="pool exhausted",
            recommended_actions=["increase pool"],
        )

        assert out.executive_summary
