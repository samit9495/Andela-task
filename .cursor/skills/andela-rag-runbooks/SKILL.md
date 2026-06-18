---
name: andela-rag-runbooks
description: Build and evaluate the runbook RAG engine — loader, embedder, retriever, citation. Use when adding runbooks, changing the embedder, or wiring RAG into the Remediation Agent.
---

# Andela RAG Runbooks

## Trigger

Use when asked to: load runbooks, build/swap the embedder, debug retrieval, wire RAG into the Remediation Agent, evaluate retrieval quality. Triggered by `RAG:` shortcut.

## Context

RAG (Req. doc Component 9) injects retrieved runbooks into the Remediation Agent's prompt so remediations are grounded in the team's documented procedures.

```
data/runbooks/*.md  ─►  RunbookLoader  ─►  Embedder  ─►  Retriever  ─►  Remediation Agent
```

This skill scaffolds each piece test-first.

## Step 0 — Define the runbook source format

`data/runbooks/database_timeout.md`:

```markdown
---
title: Database Timeout
category: database
keywords: [timeout, connection, pool, exhaustion]
version: 1
---

# Database Timeout

## Symptoms
- Errors with "Database timeout" or "connection refused"

## Investigation
1. Check connection pool metrics
2. Inspect long-running queries

## Remediation
1. Increase the connection pool size
2. Restart the worker pool
3. Investigate query plans
```

## Step 1 — RED: loader test

```python
# tests/unit/test_rag_loader.py
class TestRunbookLoader:
    def test_loads_a_runbook_with_frontmatter(self, tmp_path):
        (tmp_path / "x.md").write_text("---\ntitle: X\ncategory: database\n---\n# Body\n")
        loader = RunbookLoader(tmp_path)
        runbooks = loader.load_all()
        assert len(runbooks) == 1
        assert runbooks[0].title == "X"
        assert runbooks[0].category == "database"
```

Run it, fail it, commit `test: ...`.

## Step 2 — Implement the loader

```python
# backend/app/rag/runbook_loader.py
import yaml
from pathlib import Path
from app.models.runbook import Runbook


class RunbookLoader:
    def __init__(self, source_dir: Path):
        self.source_dir = source_dir

    def load_all(self) -> list[Runbook]:
        runbooks = []
        for path in sorted(self.source_dir.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            meta, body = self._split_frontmatter(text)
            runbooks.append(Runbook(
                source_path=str(path.name),
                title=meta["title"],
                category=meta.get("category"),
                content=body,
                content_hash=self._hash(text),
                version=meta.get("version", 1),
            ))
        return runbooks

    @staticmethod
    def _split_frontmatter(text: str) -> tuple[dict, str]:
        if not text.startswith("---"):
            return {}, text
        _, fm, body = text.split("---", 2)
        return yaml.safe_load(fm), body.strip()

    @staticmethod
    def _hash(text: str) -> str:
        from hashlib import sha256
        return sha256(text.encode("utf-8")).hexdigest()
```

## Step 3 — Define the Embedder protocol with a deterministic fake

```python
# backend/app/rag/embedder.py
from typing import Protocol
import numpy as np


class Embedder(Protocol):
    def embed(self, text: str) -> np.ndarray: ...


class HashEmbedder:
    """Deterministic, offline-friendly embedder for tests and local dev."""
    DIM = 64

    def embed(self, text: str) -> np.ndarray:
        rng = np.random.default_rng(seed=int.from_bytes(text.encode("utf-8")[:16].ljust(16, b"\x00"), "big") % (2**32))
        v = rng.standard_normal(self.DIM)
        return v / np.linalg.norm(v)
```

For production, a `GeminiEmbedder` implements the same protocol calling `text-embedding-004` via google-genai.

## Step 4 — Retriever (cosine similarity, top-K, similarity floor)

```python
# backend/app/rag/retriever.py
from dataclasses import dataclass
import numpy as np


@dataclass
class RetrievalResult:
    runbook_id: int
    title: str
    similarity: float


class Retriever:
    def __init__(self, embedder: Embedder, top_k: int = 3, min_similarity: float = 0.6):
        self.embedder = embedder
        self.top_k = top_k
        self.min_similarity = min_similarity

    def retrieve(self, query: str, runbooks: list[Runbook]) -> list[RetrievalResult]:
        q = self.embedder.embed(query)
        scored = [
            (rb, float(np.dot(q, np.asarray(rb.embedding))))
            for rb in runbooks
        ]
        # similarity floor + top-K + deterministic tie-breaks
        scored = [(rb, s) for rb, s in scored if s >= self.min_similarity]
        scored.sort(key=lambda t: (-t[1], -t[0].version, t[0].id))
        return [RetrievalResult(rb.id, rb.title, s) for rb, s in scored[: self.top_k]]
```

## Step 5 — Wire into the Remediation Agent

The Remediation Agent (per `.cursor/skills/andela-agent-workflow/SKILL.md`) accepts a list of retrieved runbooks and includes them in its prompt:

```python
runbook_excerpts = "\n\n".join(
    f"### Runbook: {rb.title}\n{_excerpt(rb.content, max_chars=800)}"
    for rb in retrieved
)
```

The agent's `Remediation` Pydantic output has a `references: list[RunbookReference]` field. The Executive Summary Agent aggregates these into `IncidentReport.runbook_references`.

## Step 6 — Tests

- `tests/unit/test_rag_loader.py` — frontmatter parsing, content hash on change.
- `tests/unit/test_rag_embedder.py` — deterministic fake produces stable vectors; `GeminiEmbedder` is mocked.
- `tests/unit/test_rag_retriever.py` — top-K, similarity floor, tie-break ordering.
- `tests/unit/test_remediation_agent_with_rag.py` — retrieved runbooks appear in prompt; references in output.
- `tests/ai_eval/test_remediation_quality.py` — rubric: does the remediation use info from the retrieved runbook?

## Step 7 — Citation enforcement

If the Remediation Agent's output does not cite at least one retrieved runbook, log a warning. Do not block the response — the Executive Summary Agent can still produce a report — but flag for review.

```python
if retrieved and not output.references:
    logger.warning(
        "Remediation produced no runbook references despite %d retrieved",
        len(retrieved),
    )
```

## Anti-patterns

- Calling `genai.Client().models.embed_content(...)` directly from the retriever. Go through `Embedder`.
- Returning runbooks below the similarity floor "to be helpful". Better to return fewer.
- Forgetting to refresh embeddings when a runbook MD file changes (the loader hashes content; the loader re-embeds when the hash changes).
- Embedding user-supplied event content into the runbook store. Runbooks are operator-authored only.

## Checklist

- [ ] Runbook MD files have frontmatter with title/category/version
- [ ] `RunbookLoader` is idempotent (same input → same output, content-hashed)
- [ ] `Embedder` is a protocol; `HashEmbedder` for tests, `GeminiEmbedder` for prod
- [ ] `Retriever` honors top-K AND `min_similarity`
- [ ] Tie-breaks are deterministic (similarity desc, version desc, id asc)
- [ ] Remediation Agent prompt includes runbook excerpts in delimited blocks
- [ ] `Remediation.references` populated; warning logged if empty after retrieval
- [ ] Unit + AI evaluation tests added

## See also

- Rule: `.cursor/rules/andela-rag.mdc`
- Rule: `.cursor/rules/andela-agentic-ai.mdc`
- Rule: `.cursor/rules/andela-security.mdc` (delimit untrusted input)
- Skill: `.cursor/skills/andela-agent-workflow/SKILL.md`
