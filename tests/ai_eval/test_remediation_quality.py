"""AI evaluation: remediation is grounded in a retrieved runbook (deterministic)."""

import pytest
from backend.app.rag.embedder import HashingEmbedder
from backend.app.rag.retriever import RunbookRetriever
from backend.app.rag.runbook_loader import RunbookLoader
from backend.app.triage.agents.remediation_agent import RemediationAgent
from backend.app.triage.mock_ai_client import MockAIClient
from backend.app.triage.prompt_log import NullPromptLog


@pytest.mark.ai_eval
class TestRemediationQuality:
    def test_database_outage_remediation_cites_database_runbook(self):
        runbooks = RunbookLoader("data/runbooks").load_all()
        retriever = RunbookRetriever(HashingEmbedder(), runbooks, top_k=3, min_similarity=0.0)
        retrieved = retriever.retrieve("database connection pool timeout query deadlock")

        agent = RemediationAgent(MockAIClient(), NullPromptLog())
        result = agent.recommend(
            incident_summary="payment-api database timeouts",
            root_cause="connection pool exhausted",
            retrieved=retrieved,
        )

        assert result.recommended_actions
        assert any(ref.slug == "database_timeout" for ref in result.references)
