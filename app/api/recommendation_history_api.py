from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.recommendation_history_schema import (
    RecommendationHistoryCreate,
    RecommendationHistoryResponse,
)
from app.services.recommendation_history_service import RecommendationHistoryService

router = APIRouter(prefix="/recommendation-histories", tags=["recommendation-histories"])


@router.post("", response_model=list[RecommendationHistoryResponse], status_code=201)
async def create_recommendation_histories(
    payload: RecommendationHistoryCreate,
    db: AsyncSession = Depends(get_db),
):
    return await RecommendationHistoryService(db).create_recommendation_histories(
        payload
    )


@router.get("", response_model=list[RecommendationHistoryResponse])
async def list_recommendation_histories(
    recommendation_id: int | None = None,
    user_id: int | None = None,
    chrstn_mno: str | None = None,
    selected: bool | None = None,
    recommendation_type: str | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    return await RecommendationHistoryService(db).get_recommendation_histories(
        recommendation_id=recommendation_id,
        user_id=user_id,
        chrstn_mno=chrstn_mno,
        selected=selected,
        recommendation_type=recommendation_type,
        limit=limit,
        offset=offset,
    )
