"""Unit tests for the runbook retriever."""

from backend.app.rag.embedder import HashingEmbedder
from backend.app.rag.retriever import RunbookRetriever, build_runbook_retriever
from backend.app.rag.runbook_loader import Runbook

_RUNBOOKS = [
    Runbook(
        slug="database_timeout",
        title="Database Timeout",
        category="database",
        keywords=["database", "timeout", "pool", "connection"],
        content="Database timeout from connection pool exhaustion. Increase pool size.",
    ),
    Runbook(
        slug="jwt_authentication",
        title="Authentication Failures",
        category="authentication",
        keywords=["auth", "jwt", "token", "login"],
        content="Authentication failures from invalid jwt tokens and login errors.",
    ),
    Runbook(
        slug="disk_full",
        title="Disk Full",
        category="infrastructure",
        keywords=["disk", "storage", "space"],
        content="Disk full, no space left on device, rotate logs.",
    ),
]


class TestRunbookRetriever:
    def test_retrieves_database_runbook_for_database_query(self):
        retriever = RunbookRetriever(HashingEmbedder(), _RUNBOOKS, top_k=2, min_similarity=0.0)

        results = retriever.retrieve("database connection pool timeout")

        assert results[0].slug == "database_timeout"

    def test_respects_top_k(self):
        retriever = RunbookRetriever(HashingEmbedder(), _RUNBOOKS, top_k=1, min_similarity=0.0)

        assert len(retriever.retrieve("database timeout")) == 1

    def test_min_similarity_filters_everything(self):
        retriever = RunbookRetriever(HashingEmbedder(), _RUNBOOKS, top_k=3, min_similarity=1.1)

        assert retriever.retrieve("database timeout") == []

    def test_empty_runbooks_returns_empty(self):
        retriever = RunbookRetriever(HashingEmbedder(), [], top_k=3, min_similarity=0.0)

        assert retriever.retrieve("anything") == []

    def test_factory_loads_runbooks_from_disk(self):
        retriever = build_runbook_retriever()

        results = retriever.retrieve("database connection pool timeout query deadlock")

        assert any(r.slug == "database_timeout" for r in results)
