from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.recommendation_history_schema import (
    RecommendationHistoryCreate,
    RecommendationHistoryResponse,
)
from app.services.recommendation_history_service import RecommendationHistoryService

router = APIRouter(prefix="/recommendation-histories", tags=["recommendation-histories"])


@router.post("", response_model=RecommendationHistoryResponse)
async def create_recommendation_history(
    payload: RecommendationHistoryCreate,
    db: AsyncSession = Depends(get_db),
):
    return await RecommendationHistoryService(db).create_recommendation_history(payload)


@router.get("", response_model=list[RecommendationHistoryResponse])
async def list_recommendation_histories(
    recommendation_id: int | None = None,
    user_id: int | None = None,
    vehicle_id: int | None = None,
    hydrogen_station_id: int | None = None,
    selected: bool | None = None,
    recommendation_type: str | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    return await RecommendationHistoryService(db).get_recommendation_histories(
        recommendation_id,
        user_id,
        vehicle_id,
        hydrogen_station_id,
        selected,
        recommendation_type,
        limit,
        offset,
    )
