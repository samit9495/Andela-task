"""Health endpoint. Reports liveness, version, and the active AI mode."""

from fastapi import APIRouter, Depends

from backend.app.core.config import Settings, get_settings
from backend.app.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """Return service liveness, version, and whether AI runs in mock or live mode."""
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        ai_mode=settings.ai_mode,
    )
