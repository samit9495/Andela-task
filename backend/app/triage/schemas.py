"""Structured outputs for the triage pipeline.

Every agent returns one of these Pydantic models — never free-form text — so the
LLM boundary stays a single ``complete_structured`` method and all output is
schema-validated.
"""

from pydantic import BaseModel, ConfigDict, Field

from backend.app.models.enums import IncidentCategory


class ClassificationOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: IncidentCategory
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str = Field(default="", max_length=2000)


class RootCauseAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    root_cause: str = Field(max_length=2000)
    confidence: float = Field(ge=0.0, le=1.0)


class RemediationActions(BaseModel):
    """The Remediation Agent's LLM-produced output (actions only)."""

    model_config = ConfigDict(extra="forbid")

    recommended_actions: list[str] = Field(min_length=1)


class RunbookReference(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    slug: str
    title: str


class RemediationOutput(BaseModel):
    """The full remediation result: actions plus runbook citations."""

    model_config = ConfigDict(extra="forbid")

    recommended_actions: list[str]
    references: list[RunbookReference] = Field(default_factory=list)


class ExecutiveSummaryOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    executive_summary: str = Field(max_length=4000)


class IncidentReport(BaseModel):
    """Aggregate triage result for an incident."""

    model_config = ConfigDict(extra="forbid")

    category: IncidentCategory
    confidence: float = Field(ge=0.0, le=1.0)
    root_cause: str
    recommended_actions: list[str]
    references: list[RunbookReference]
    executive_summary: str
