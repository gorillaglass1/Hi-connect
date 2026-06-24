from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.nearest_recommendation_schema import (
    NearestRecommendationRequest,
    NearestRecommendationResponse,
)
from app.services.nearest_recommendation_service import NearestRecommendationService

router = APIRouter(prefix="/nearest-recommendation", tags=["nearest-recommendation"])


@router.post("", response_model=NearestRecommendationResponse)
async def get_nearest_recommendation(
    request: NearestRecommendationRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    잔량 충분 화면용 단순 최저가 추천.
    현재 위치 반경 내 활성 충전소 중 최저가 1곳을 골라
    연료 잔량 기반 상태(sufficient/recommend/urgent)와 함께 리턴합니다.
    """
    return await NearestRecommendationService(db).get_nearest_cheapest(request)
