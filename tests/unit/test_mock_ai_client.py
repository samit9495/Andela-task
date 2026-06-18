"""Unit tests for the MockAIClient heuristic fallback."""

import pytest
from backend.app.core.exceptions import LLMResponseInvalid
from backend.app.models.enums import IncidentCategory
from backend.app.triage.mock_ai_client import MockAIClient
from backend.app.triage.schemas import (
    ClassificationOutput,
    ExecutiveSummaryOutput,
    RemediationActions,
    RootCauseAnalysis,
)


class TestMockAIClient:
    def test_classifies_database_keywords(self):
        client = MockAIClient()

        out = client.complete_structured(
            prompt="Incident: database connection pool timeout",
            schema=ClassificationOutput,
            request_id="r",
        )

        assert out.category == IncidentCategory.DATABASE

    def test_classifies_authentication_keywords(self):
        client = MockAIClient()

        out = client.complete_structured(
            prompt="repeated jwt token invalid, login failed 401",
            schema=ClassificationOutput,
            request_id="r",
        )

        assert out.category == IncidentCategory.AUTHENTICATION

    def test_root_cause_is_populated(self):
        client = MockAIClient()

        out = client.complete_structured(
            prompt="database timeout", schema=RootCauseAnalysis, request_id="r"
        )

        assert out.root_cause

    def test_remediation_actions_present(self):
        client = MockAIClient()

        out = client.complete_structured(
            prompt="database timeout", schema=RemediationActions, request_id="r"
        )

        assert len(out.recommended_actions) >= 1

    def test_summary_present(self):
        client = MockAIClient()

        out = client.complete_structured(
            prompt="anything", schema=ExecutiveSummaryOutput, request_id="r"
        )

        assert out.executive_summary

    def test_unsupported_schema_raises(self):
        client = MockAIClient()

        with pytest.raises(LLMResponseInvalid):
            client.complete_structured(
                prompt="x", schema=ClassificationOutput.__mro__[1], request_id="r"
            )

    def test_explicit_category_hint_overrides_keyword_heuristic(self):
        """Chained-agent prompts carry `Category: <name>` so downstream stays consistent."""
        client = MockAIClient()
        prompt = (
            "Some preamble.\n<<<INPUT>>>\nCategory: authentication\n"
            "Incident summary: a database pool timeout query.\n<<<END>>>\n"
        )

        out = client.complete_structured(prompt=prompt, schema=ClassificationOutput, request_id="r")

        assert out.category == IncidentCategory.AUTHENTICATION

    def test_unknown_explicit_category_falls_through_to_keywords(self):
        """A malformed Category: value must not crash; heuristic still wins."""
        client = MockAIClient()
        prompt = (
            "<<<INPUT>>>\nCategory: not_a_real_category\n"
            "Incident summary: database pool timeout query.\n<<<END>>>\n"
        )

        out = client.complete_structured(prompt=prompt, schema=ClassificationOutput, request_id="r")

        assert out.category == IncidentCategory.DATABASE
