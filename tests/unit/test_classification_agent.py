"""Unit tests for the Classification Agent."""

import pytest

from backend.app.core.exceptions import LLMAuthError, LLMRateLimited, LLMResponseInvalid
from backend.app.models.enums import IncidentCategory
from backend.app.triage.agents.classification_agent import ClassificationAgent
from backend.app.triage.llm_client import FakeLLMClient
from backend.app.triage.prompt_log import NullPromptLog
from backend.app.triage.schemas import ClassificationOutput


class TestClassificationAgent:
    def test_returns_llm_classification_and_builds_prompt(self):
        fake = FakeLLMClient()
        fake.register_for_schema(
            ClassificationOutput,
            ClassificationOutput(
                category=IncidentCategory.DATABASE, confidence=0.9, reasoning="db"
            ),
        )
        agent = ClassificationAgent(fake, NullPromptLog())

        out = agent.classify(
            incident_summary="payment-api database timeouts",
            top_events=[("Database timeout", 70, "ERROR")],
        )

        assert out.category == IncidentCategory.DATABASE
        assert "payment-api" in fake.last_prompt
        assert "Database timeout" in fake.last_prompt

    def test_falls_back_to_unknown_on_failure(self):
        fake = FakeLLMClient()
        fake.set_to_raise(LLMResponseInvalid("bad"))
        agent = ClassificationAgent(fake, NullPromptLog())

        out = agent.classify(incident_summary="x", top_events=[])

        assert out.category == IncidentCategory.UNKNOWN
        assert out.confidence == 0.0

    @pytest.mark.parametrize(
        "exc",
        [LLMRateLimited("quota"), LLMAuthError("forbidden")],
    )
    def test_falls_back_on_rate_limit_and_auth_errors(self, exc):
        fake = FakeLLMClient()
        fake.set_to_raise(exc)
        agent = ClassificationAgent(fake, NullPromptLog())

        out = agent.classify(incident_summary="x", top_events=[])

        assert out.category == IncidentCategory.UNKNOWN
        assert out.confidence == 0.0
