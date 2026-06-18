"""Unit tests for GeminiLLMClient (with a stubbed genai client, no network)."""

import pytest
from backend.app.core.exceptions import (
    LLMAuthError,
    LLMRateLimited,
    LLMResponseInvalid,
    LLMTimeout,
)
from backend.app.models.enums import IncidentCategory
from backend.app.triage.gemini_client import GeminiLLMClient
from backend.app.triage.schemas import ClassificationOutput
from google.genai import errors as genai_errors


def _api_error(cls: type[genai_errors.APIError], code: int, status: str = "") -> Exception:
    """Build a google.genai APIError-family exception without a real HTTP response."""
    exc = cls.__new__(cls)
    exc.code = code
    exc.status = status or "ERROR"
    exc.message = f"stub {code}"
    exc.details = {}
    exc.response = None
    Exception.__init__(exc, f"{code} {exc.status}. stub")
    return exc


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

    def test_rate_limit_429_raises_llm_rate_limited(self):
        client = _StubClient(exc=_api_error(genai_errors.ClientError, 429, "RESOURCE_EXHAUSTED"))
        gemini = GeminiLLMClient(api_key="k", model="m", client=client)

        with pytest.raises(LLMRateLimited):
            gemini.complete_structured(prompt="p", schema=ClassificationOutput, request_id="r")

    def test_auth_401_raises_llm_auth_error(self):
        client = _StubClient(exc=_api_error(genai_errors.ClientError, 401, "UNAUTHENTICATED"))
        gemini = GeminiLLMClient(api_key="k", model="m", client=client)

        with pytest.raises(LLMAuthError):
            gemini.complete_structured(prompt="p", schema=ClassificationOutput, request_id="r")

    def test_auth_403_raises_llm_auth_error(self):
        client = _StubClient(exc=_api_error(genai_errors.ClientError, 403, "PERMISSION_DENIED"))
        gemini = GeminiLLMClient(api_key="k", model="m", client=client)

        with pytest.raises(LLMAuthError):
            gemini.complete_structured(prompt="p", schema=ClassificationOutput, request_id="r")

    def test_other_4xx_raises_response_invalid(self):
        client = _StubClient(exc=_api_error(genai_errors.ClientError, 400, "INVALID_ARGUMENT"))
        gemini = GeminiLLMClient(api_key="k", model="m", client=client)

        with pytest.raises(LLMResponseInvalid):
            gemini.complete_structured(prompt="p", schema=ClassificationOutput, request_id="r")

    def test_server_5xx_raises_llm_timeout(self):
        client = _StubClient(exc=_api_error(genai_errors.ServerError, 503, "UNAVAILABLE"))
        gemini = GeminiLLMClient(api_key="k", model="m", client=client)

        with pytest.raises(LLMTimeout):
            gemini.complete_structured(prompt="p", schema=ClassificationOutput, request_id="r")

    def test_auth_error_is_not_retried(self):
        """An auth failure must raise immediately without consuming retry budget."""

        class _CountingModels:
            def __init__(self) -> None:
                self.calls = 0

            def generate_content(self, **kwargs):
                self.calls += 1
                raise _api_error(genai_errors.ClientError, 401, "UNAUTHENTICATED")

        class _CountingClient:
            def __init__(self) -> None:
                self.models = _CountingModels()

        client = _CountingClient()
        gemini = GeminiLLMClient(api_key="k", model="m", client=client, max_retries=3)

        with pytest.raises(LLMAuthError):
            gemini.complete_structured(prompt="p", schema=ClassificationOutput, request_id="r")
        assert client.models.calls == 1
