"""Deterministic, offline text embedding for runbook retrieval.

``HashingEmbedder`` is a hashing bag-of-words vectorizer: it needs no corpus fit
and no network, yet cosine similarity reflects shared vocabulary. The ``Embedder``
protocol lets a real embedding model (e.g. Gemini ``text-embedding-004``) drop in
later without touching the retriever.
"""

import re
from hashlib import md5
from typing import Protocol

import numpy as np

_TOKEN_RE = re.compile(r"[a-z0-9]+")


class Embedder(Protocol):
    def embed(self, text: str) -> np.ndarray: ...


class HashingEmbedder:
    """Hashing bag-of-words embedder; deterministic across processes."""

    def __init__(self, dimensions: int = 256) -> None:
        self.dimensions = dimensions

    def embed(self, text: str) -> np.ndarray:
        vector = np.zeros(self.dimensions, dtype=float)
        for token in _TOKEN_RE.findall(text.lower()):
            vector[self._bucket(token)] += 1.0
        norm = float(np.linalg.norm(vector))
        if norm == 0.0:
            return vector
        return vector / norm

    def _bucket(self, token: str) -> int:
        digest = md5(token.encode("utf-8")).hexdigest()
        return int(digest, 16) % self.dimensions
