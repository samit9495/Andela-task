"""The only module permitted to talk to Google Gemini.

Wraps ``google-genai`` behind the ``LLMClient`` protocol with structured output,
a single retry, and translation of provider failures into domain exceptions.
"""

from typing import Any

from google import genai
from google.genai import types
from pydantic import ValidationError

from backend.app.core.exceptions import LLMResponseInvalid, LLMTimeout
from backend.app.triage.llm_client import T


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
        last_error: LLMResponseInvalid | LLMTimeout = LLMTimeout("no attempt executed")
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
        raise last_error
