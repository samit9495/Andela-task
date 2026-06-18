"""The only module permitted to talk to Google Gemini.

Wraps ``google-genai`` behind the ``LLMClient`` protocol with structured output,
a single retry, and translation of provider failures into domain exceptions.
"""

from typing import Any

from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from pydantic import ValidationError

from backend.app.core.exceptions import (
    DomainError,
    LLMAuthError,
    LLMRateLimited,
    LLMResponseInvalid,
    LLMTimeout,
)
from backend.app.triage.llm_client import T

_AUTH_CODES = {401, 403}


def _translate_api_error(exc: genai_errors.APIError) -> DomainError:
    """Map a google-genai APIError to a domain exception by HTTP status."""
    code = getattr(exc, "code", None) or 0
    detail = str(exc)
    if code in _AUTH_CODES:
        return LLMAuthError(detail)
    if code == 429:
        return LLMRateLimited(detail)
    if isinstance(exc, genai_errors.ServerError):
        return LLMTimeout(detail)
    return LLMResponseInvalid(detail)


class GeminiLLMClient:
    """Gemini-backed ``LLMClient`` using JSON structured output."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        client: Any | None = None,
        max_retries: int = 1,
    ) -> None:
        self._client = client if client is not None else genai.Client(api_key=api_key)
        self._model = model
        self._max_retries = max_retries

    def complete_structured(
        self,
        *,
        prompt: str,
        schema: type[T],
        temperature: float = 0.0,
        max_tokens: int = 1024,
        request_id: str,
    ) -> T:
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=schema,
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        last_error: DomainError = LLMTimeout("no attempt executed")
        for _ in range(self._max_retries + 1):
            try:
                response = self._client.models.generate_content(
                    model=self._model, contents=prompt, config=config
                )
                return schema.model_validate_json(response.text)
            except TimeoutError as exc:
                last_error = LLMTimeout(str(exc))
            except (ValidationError, ValueError):
                last_error = LLMResponseInvalid("structured output failed schema validation")
            except genai_errors.APIError as exc:
                translated = _translate_api_error(exc)
                # Auth failures are non-retryable: raise immediately.
                if isinstance(translated, LLMAuthError):
                    raise translated from exc
                last_error = translated
        raise last_error
