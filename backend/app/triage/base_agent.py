"""Shared agent machinery: timing, logging, and deterministic fallback.

Every agent extends ``StructuredAgent`` and calls ``_complete`` so the prompt
logging and LLM failure handling live in exactly one place (DRY).
"""

from time import perf_counter

from backend.app.core.exceptions import LLMRateLimited, LLMResponseInvalid, LLMTimeout
from backend.app.triage.llm_client import LLMClient, T
from backend.app.triage.prompt_log import PromptRecorder

_LLM_FAILURES = (LLMTimeout, LLMResponseInvalid, LLMRateLimited)


class StructuredAgent:
    NAME: str = "agent"

    def __init__(
        self, llm: LLMClient, prompt_log: PromptRecorder, *, incident_id: int | None = None
    ) -> None:
        self._llm = llm
        self._log = prompt_log
        self._incident_id = incident_id

    def _complete(
        self, *, prompt: str, schema: type[T], prompt_version: str, max_tokens: int = 1024
    ) -> T | None:
        """Run the LLM call; log success/failure; return ``None`` on LLM failure."""
        request_id = self._log.next_request_id()
        start = perf_counter()
        try:
            output = self._llm.complete_structured(
                prompt=prompt,
                schema=schema,
                temperature=0.0,
                max_tokens=max_tokens,
                request_id=request_id,
            )
        except _LLM_FAILURES as exc:
            self._log.record(
                agent=self.NAME,
                prompt_version=prompt_version,
                prompt=prompt,
                response=None,
                status=type(exc).__name__,
                latency_ms=_elapsed_ms(start),
                incident_id=self._incident_id,
            )
            return None
        self._log.record(
            agent=self.NAME,
            prompt_version=prompt_version,
            prompt=prompt,
            response=output,
            status="ok",
            latency_ms=_elapsed_ms(start),
            incident_id=self._incident_id,
        )
        return output


def _elapsed_ms(start: float) -> int:
    return int((perf_counter() - start) * 1000)


def format_top_events(top_events: list[tuple[str, int, str]]) -> str:
    if not top_events:
        return "- (none)"
    return "\n".join(
        f"- {signature}: count={count}, level={level}" for signature, count, level in top_events
    )
