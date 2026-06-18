"""The LLM boundary.

Every triage agent depends on the ``LLMClient`` protocol, never on a concrete
provider. ``FakeLLMClient`` is the deterministic test double; the real Gemini
implementation lives in ``gemini_client.py`` and the offline heuristic in
``mock_ai_client.py``.
"""

from typing import Protocol, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMClient(Protocol):
    """The only contract through which the platform talks to an LLM."""

    def complete_structured(
        self,
        *,
        prompt: str,
        schema: type[T],
        temperature: float = 0.0,
        max_tokens: int = 1024,
        request_id: str,
    ) -> T:
        """Return a schema-validated structured output for ``prompt``."""
        ...


class FakeLLMClient:
    """Deterministic test double: returns canned outputs registered per schema."""

    def __init__(self) -> None:
        self._by_schema: dict[type[BaseModel], BaseModel] = {}
        self._exc: Exception | None = None
        self.prompts: list[str] = []

    def register_for_schema(self, schema: type[BaseModel], output: BaseModel) -> None:
        self._by_schema[schema] = output

    def set_to_raise(self, exc: Exception) -> None:
        self._exc = exc

    @property
    def last_prompt(self) -> str | None:
        return self.prompts[-1] if self.prompts else None

    def complete_structured(
        self,
        *,
        prompt: str,
        schema: type[T],
        temperature: float = 0.0,
        max_tokens: int = 1024,
        request_id: str,
    ) -> T:
        self.prompts.append(prompt)
        if self._exc is not None:
            raise self._exc
        if schema not in self._by_schema:
            raise KeyError(f"no canned output registered for {schema.__name__}")
        output = self._by_schema[schema]
        assert isinstance(output, schema)
        return output
