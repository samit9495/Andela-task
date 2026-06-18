"""The single sink for LLM interaction logging.

Every agent call is recorded here: one ``llm_evaluations`` row and one appended
block in ``docs/llm_prompts.md``. No agent writes the markdown file directly.
"""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol
from uuid import uuid4

from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.models.llm_evaluation import LLMEvaluation
from backend.app.repositories.llm_evaluation_repository import LLMEvaluationRepository


class PromptRecorder(Protocol):
    """The logging contract agents depend on (satisfied by PromptLog and NullPromptLog)."""

    def next_request_id(self) -> str: ...

    def record(
        self,
        *,
        agent: str,
        prompt_version: str,
        prompt: str,
        response: BaseModel | None,
        status: str,
        latency_ms: int = 0,
        incident_id: int | None = None,
        tokens_in: int = 0,
        tokens_out: int = 0,
    ) -> Any: ...


class PromptLog:
    """Persists prompts/responses to the database and the audit markdown file."""

    def __init__(self, db: Session, *, model: str, log_path: str | Path) -> None:
        self._db = db
        self._repo = LLMEvaluationRepository(db)
        self._model = model
        self._path = Path(log_path)

    def next_request_id(self) -> str:
        return uuid4().hex

    def record(
        self,
        *,
        agent: str,
        prompt_version: str,
        prompt: str,
        response: BaseModel | None,
        status: str,
        latency_ms: int = 0,
        incident_id: int | None = None,
        tokens_in: int = 0,
        tokens_out: int = 0,
    ) -> LLMEvaluation:
        response_text = response.model_dump_json() if response is not None else ""
        evaluation = LLMEvaluation(
            incident_id=incident_id,
            agent=agent,
            prompt_version=prompt_version,
            prompt=prompt,
            response=response_text,
            model=self._model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            latency_ms=latency_ms,
            status=status,
        )
        self._repo.add(evaluation)
        self._db.commit()
        self._db.refresh(evaluation)
        self._append_markdown(evaluation)
        return evaluation

    def _append_markdown(self, evaluation: LLMEvaluation) -> None:
        timestamp = datetime.now(tz=UTC).isoformat()
        block = (
            f"\n## {timestamp} - {evaluation.agent} {evaluation.prompt_version} - "
            f"incident_id={evaluation.incident_id}\n"
            f"### Prompt\n{evaluation.prompt}\n"
            f"### Response\n{evaluation.response}\n"
            f"### Metrics\n"
            f"model={evaluation.model} tokens_in={evaluation.tokens_in} "
            f"tokens_out={evaluation.tokens_out} latency_ms={evaluation.latency_ms} "
            f"status={evaluation.status}\n"
        )
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(block)


class NullPromptLog:
    """No-op recorder for unit tests that do not assert on logging."""

    def next_request_id(self) -> str:
        return "test-request"

    def record(
        self,
        *,
        agent: str,
        prompt_version: str,
        prompt: str,
        response: BaseModel | None,
        status: str,
        latency_ms: int = 0,
        incident_id: int | None = None,
        tokens_in: int = 0,
        tokens_out: int = 0,
    ) -> None:
        return None
