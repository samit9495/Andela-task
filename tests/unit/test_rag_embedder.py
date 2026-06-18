"""Unit tests for the deterministic HashingEmbedder."""

import numpy as np
from backend.app.rag.embedder import HashingEmbedder


class TestHashingEmbedder:
    def test_is_deterministic(self):
        embedder = HashingEmbedder()

        first = embedder.embed("database connection pool timeout")
        second = embedder.embed("database connection pool timeout")

        assert np.array_equal(first, second)

    def test_unit_norm(self):
        vector = HashingEmbedder().embed("database timeout")

        assert np.isclose(np.linalg.norm(vector), 1.0)

    def test_similar_text_scores_higher_than_dissimilar(self):
        embedder = HashingEmbedder()
        query = embedder.embed("database connection pool timeout")
        related = embedder.embed("database pool exhausted, query timeout")
        unrelated = embedder.embed("authentication jwt token login failure")

        assert float(query @ related) > float(query @ unrelated)

    def test_empty_text_returns_zero_vector(self):
        vector = HashingEmbedder().embed("")

        assert np.linalg.norm(vector) == 0.0
