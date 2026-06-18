"""Unit tests for the FakeLLMClient test double."""

import pytest
from backend.app.core.exceptions import LLMResponseInvalid
from backend.app.models.enums import IncidentCategory
from backend.app.triage.llm_client import FakeLLMClient
from backend.app.triage.schemas import ClassificationOutput


def _output():
    return ClassificationOutput(category=IncidentCategory.DATABASE, confidence=0.9, reasoning="x")


class TestFakeLLMClient:
    def test_returns_registered_output_and_captures_prompt(self):
        fake = FakeLLMClient()
        fake.register_for_schema(ClassificationOutput, _output())

        result = fake.complete_structured(prompt="p", schema=ClassificationOutput, request_id="r")

        assert result.category == IncidentCategory.DATABASE
        assert fake.last_prompt == "p"

    def test_raises_when_configured(self):
        fake = FakeLLMClient()
        fake.set_to_raise(LLMResponseInvalid("bad json"))

        with pytest.raises(LLMResponseInvalid):
            fake.complete_structured(prompt="p", schema=ClassificationOutput, request_id="r")

    def test_unregistered_schema_raises_key_error(self):
        fake = FakeLLMClient()

        with pytest.raises(KeyError):
            fake.complete_structured(prompt="p", schema=ClassificationOutput, request_id="r")
