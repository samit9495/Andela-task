"""Unit tests for GeminiLLMClient (with a stubbed genai client, no network)."""

import pytest
from backend.app.core.exceptions import LLMResponseInvalid, LLMTimeout
from backend.app.models.enums import IncidentCategory
from backend.app.triage.gemini_client import GeminiLLMClient
from backend.app.triage.schemas import ClassificationOutput


class _StubResponse:
    def __init__(self, text: str) -> None:
        self.text = text


class _StubModels:
    def __init__(self, text: str | None = None, exc: Exception | None = None) -> None:
        self._text = text
        self._exc = exc

    def generate_content(self, **kwargs):
        if self._exc is not None:
            raise self._exc
        return _StubResponse(self._text or "")


class _StubClient:
    def __init__(self, text: str | None = None, exc: Exception | None = None) -> None:
        self.models = _StubModels(text=text, exc=exc)


class TestGeminiLLMClient:
    def test_parses_structured_json_into_schema(self):
        client = _StubClient(text='{"category": "database", "confidence": 0.9, "reasoning": "x"}')
        gemini = GeminiLLMClient(api_key="k", model="m", client=client)

        out = gemini.complete_structured(prompt="p", schema=ClassificationOutput, request_id="r")

        assert out.category == IncidentCategory.DATABASE
        assert out.confidence == 0.9

    def test_invalid_json_raises_response_invalid(self):
        client = _StubClient(text="not json at all")
        gemini = GeminiLLMClient(api_key="k", model="m", client=client)

        with pytest.raises(LLMResponseInvalid):
            gemini.complete_structured(prompt="p", schema=ClassificationOutput, request_id="r")

    def test_timeout_raises_llm_timeout(self):
        client = _StubClient(exc=TimeoutError("deadline exceeded"))
        gemini = GeminiLLMClient(api_key="k", model="m", client=client)

        with pytest.raises(LLMTimeout):
            gemini.complete_structured(prompt="p", schema=ClassificationOutput, request_id="r")
