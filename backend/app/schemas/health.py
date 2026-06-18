"""Response schema for the health endpoint."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Liveness payload returned by ``GET /health``."""

    status: str
    version: str
    ai_mode: str
