"""Unit tests for the domain exception hierarchy."""

import pytest
from backend.app.core.exceptions import (
    DomainError,
    EventValidationError,
    IncidentNotFound,
    LLMResponseInvalid,
    LLMTimeout,
    TriageFailed,
)


class TestDomainExceptions:
    @pytest.mark.parametrize(
        "exc_type",
        [
            EventValidationError,
            IncidentNotFound,
            TriageFailed,
            LLMTimeout,
            LLMResponseInvalid,
        ],
    )
    def test_subclasses_inherit_from_domain_error(self, exc_type):
        assert issubclass(exc_type, DomainError)

    def test_domain_error_carries_a_message(self):
        error = IncidentNotFound("incident 42 not found")

        assert str(error) == "incident 42 not found"
