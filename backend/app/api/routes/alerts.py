"""Alert query endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from backend.app.api.deps import get_alert_repository
from backend.app.repositories.alert_repository import AlertRepository
from backend.app.schemas.alert import AlertRead

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertRead])
def list_alerts(
    incident_id: Annotated[int | None, Query(ge=1)] = None,
    repo: AlertRepository = Depends(get_alert_repository),
) -> list[AlertRead]:
    alerts = repo.list(incident_id=incident_id)
    return [AlertRead.model_validate(alert) for alert in alerts]
