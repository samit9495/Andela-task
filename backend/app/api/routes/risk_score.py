"""Platform risk-score endpoint."""

from fastapi import APIRouter, Depends

from backend.app.api.deps import get_risk_score_service
from backend.app.risk.risk_score_service import RiskScoreService
from backend.app.schemas.risk import RiskScoreResponse

router = APIRouter(prefix="/api/v1/risk-score", tags=["risk"])


@router.get("", response_model=RiskScoreResponse)
def get_risk_score(
    service: RiskScoreService = Depends(get_risk_score_service),
) -> RiskScoreResponse:
    return service.calculate()
