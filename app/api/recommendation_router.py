from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.recommendation_request_schemas import (
    RecommendationSearchRequest,
    RecommendedStationResponse,
)
from app.services.recommendation_service import RecommendationService

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("/personalized", response_model=list[RecommendedStationResponse])
async def search_personalized_recommendations(
    request: RecommendationSearchRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    사용자의 현재 위치, 목적지, 주행가능거리 및 개인 가중치를 활용하여
    반경 필터링 후 맞춤형 정렬 목록을 리턴합니다.
    자연어 쿼리(nl_query)가 포함된 경우 Gemini AI Text-to-SQL 필터링을 거치게 됩니다.
    """
    service = RecommendationService(db)
    return await service.get_personalized_recommendations(request)
