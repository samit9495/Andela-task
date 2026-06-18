"""Schema for the platform risk score."""

from pydantic import BaseModel, ConfigDict, Field


class RiskScoreResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    score: float = Field(ge=0.0, le=100.0)
    status: str
    error_penalty: float = Field(ge=0.0)
    alert_penalty: float = Field(ge=0.0)
    incident_penalty: float = Field(ge=0.0)
