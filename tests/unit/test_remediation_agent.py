"""Unit tests for the Remediation Agent (RAG-fed)."""

from backend.app.core.exceptions import LLMResponseInvalid
from backend.app.rag.retriever import RetrievalResult
from backend.app.triage.agents.remediation_agent import RemediationAgent
from backend.app.triage.llm_client import FakeLLMClient
from backend.app.triage.prompt_log import NullPromptLog
from backend.app.triage.schemas import RemediationActions

_RETRIEVED = [
    RetrievalResult(
        slug="database_timeout",
        title="Database Timeout",
        similarity=0.9,
        content="Increase the connection pool size. Restart the worker pool.",
    )
]


class TestRemediationAgent:
    def test_injects_runbook_and_cites_reference(self):
        fake = FakeLLMClient()
        fake.register_for_schema(
            RemediationActions,
            RemediationActions(recommended_actions=["Increase pool size"]),
        )
        agent = RemediationAgent(fake, NullPromptLog())

        out = agent.recommend(
            incident_summary="db timeouts",
            root_cause="pool exhausted",
            retrieved=_RETRIEVED,
        )

        assert out.recommended_actions == ["Increase pool size"]
        assert [ref.slug for ref in out.references] == ["database_timeout"]
        assert "Database Timeout" in fake.last_prompt
        assert "connection pool" in fake.last_prompt

    def test_falls_back_but_keeps_references(self):
        fake = FakeLLMClient()
        fake.set_to_raise(LLMResponseInvalid("bad"))
        agent = RemediationAgent(fake, NullPromptLog())

        out = agent.recommend(incident_summary="x", root_cause="y", retrieved=_RETRIEVED)

        assert len(out.recommended_actions) >= 1
        assert [ref.slug for ref in out.references] == ["database_timeout"]

    def test_no_runbooks_retrieved_yields_no_references(self):
        fake = FakeLLMClient()
        fake.register_for_schema(
            RemediationActions, RemediationActions(recommended_actions=["Investigate"])
        )
        agent = RemediationAgent(fake, NullPromptLog())

        out = agent.recommend(incident_summary="x", root_cause="y", retrieved=[])

        assert out.references == []
        assert "no runbooks matched" in fake.last_prompt
