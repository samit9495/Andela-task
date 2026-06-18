"""Domain-level exceptions mapped to HTTP responses at the API boundary.

Routes never catch these directly; ``backend.app.main`` registers handlers that
translate them into sanitized ``{"detail", "code"}`` JSON responses.
"""


class DomainError(Exception):
    """Base class for domain errors mapped to HTTP responses."""


class EventValidationError(DomainError):
    """An ingested event failed domain validation."""


class IncidentNotFound(DomainError):
    """A requested incident does not exist."""


class TriageFailed(DomainError):
    """Agentic triage could not produce a structured output."""


class LLMTimeout(DomainError):
    """The LLM call exceeded its timeout budget."""


class LLMResponseInvalid(DomainError):
    """The LLM returned a response that failed structured-output validation."""


class LLMRateLimited(DomainError):
    """The LLM provider rejected the call due to rate limiting."""
