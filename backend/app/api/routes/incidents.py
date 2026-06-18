"""Incident query endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from backend.app.api.deps import get_incident_service
from backend.app.incidents.incident_service import IncidentService
from backend.app.models.enums import IncidentStatus, Severity
from backend.app.schemas.incident import IncidentRead

router = APIRouter(prefix="/api/v1/incidents", tags=["incidents"])


@router.get("", response_model=list[IncidentRead])
def list_incidents(
    status: IncidentStatus | None = Query(default=None),
    severity: Severity | None = Query(default=None),
    service: IncidentService = Depends(get_incident_service),
) -> list[IncidentRead]:
    status_value = status.value if status is not None else None
    severity_value = severity.value if severity is not None else None
    incidents = service.list(status=status_value, severity=severity_value)
    return [IncidentRead.model_validate(incident) for incident in incidents]


@router.get("/{incident_id}", response_model=IncidentRead)
def get_incident(
    incident_id: Annotated[int, Path(ge=1)],
    service: IncidentService = Depends(get_incident_service),
) -> IncidentRead:
    return IncidentRead.model_validate(service.get(incident_id))
