from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.ai_recommendation_schema import (
    OptimizedStationRecommendationRequest,
    OptimizedStationRecommendationResponse,
)
from app.services.ai_recommendation_service import (
    OptimizedStationRecommendationService,
)

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post(
    "/optimized-stations",
    response_model=OptimizedStationRecommendationResponse,
    status_code=status.HTTP_200_OK,
)
async def recommend_optimized_station(
    payload: OptimizedStationRecommendationRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        return await OptimizedStationRecommendationService(db).recommend(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
