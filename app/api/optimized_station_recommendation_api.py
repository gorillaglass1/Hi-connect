from fastapi import APIRouter, HTTPException, status

from app.schemas.optimized_station_recommendation_schema import (
    OptimizedStationRecommendationRequest,
    OptimizedStationRecommendationResponse,
)
from app.services.optimized_station_recommendation_service import (
    OptimizedStationRecommendationService,
)

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post(
    "/optimized-stations",
    response_model=OptimizedStationRecommendationResponse,
    status_code=status.HTTP_200_OK,
)
async def recommend_optimized_station(payload: OptimizedStationRecommendationRequest):
    try:
        return await OptimizedStationRecommendationService().recommend(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
