"""Retrieves the most relevant runbooks for an incident query."""

from dataclasses import dataclass

from backend.app.core.config import Settings, get_settings
from backend.app.rag.embedder import Embedder, HashingEmbedder
from backend.app.rag.runbook_loader import Runbook, RunbookLoader


@dataclass(frozen=True)
class RetrievalResult:
    slug: str
    title: str
    similarity: float
    content: str


class RunbookRetriever:
    """Cosine-similarity retrieval over pre-embedded runbooks."""

    def __init__(
        self,
        embedder: Embedder,
        runbooks: list[Runbook],
        *,
        top_k: int = 3,
        min_similarity: float = 0.05,
    ) -> None:
        self._embedder = embedder
        self._runbooks = runbooks
        self._top_k = top_k
        self._min_similarity = min_similarity
        self._embeddings = {rb.slug: embedder.embed(self._document_text(rb)) for rb in runbooks}

    def retrieve(self, query: str) -> list[RetrievalResult]:
        query_vector = self._embedder.embed(query)
        scored = [(rb, float(query_vector @ self._embeddings[rb.slug])) for rb in self._runbooks]
        scored = [(rb, score) for rb, score in scored if score >= self._min_similarity]
        scored.sort(key=lambda pair: (-pair[1], pair[0].slug))
        return [
            RetrievalResult(slug=rb.slug, title=rb.title, similarity=score, content=rb.content)
            for rb, score in scored[: self._top_k]
        ]

    @staticmethod
    def _document_text(runbook: Runbook) -> str:
        return f"{runbook.title} {' '.join(runbook.keywords)} {runbook.content}"


def build_runbook_retriever(settings: Settings | None = None) -> RunbookRetriever:
    """Construct a retriever from runbooks on disk (used at app startup)."""
    config = settings or get_settings()
    runbooks = RunbookLoader(config.runbook_dir).load_all()
    return RunbookRetriever(
        HashingEmbedder(),
        runbooks,
        top_k=config.rag_top_k,
        min_similarity=config.rag_min_similarity,
    )
