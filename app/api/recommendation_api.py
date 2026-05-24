from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.path_range_schema import (
    PathRangeStationSearchRequest,
    PathRangeStationSearchResponse,
)
from app.schemas.recommendation_schema import (
    RecommendationDeliveryPayload,
    RecommendationSearchRequest,
    RecommendedStationResponse,
)
from app.services.path_range_specification import find_charging_stations
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


@router.post(
    "/personalized/delivery-payloads",
    response_model=list[RecommendationDeliveryPayload],
)
async def search_personalized_recommendation_delivery_payloads(
    request: RecommendationSearchRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    차량 적용 화면에서 사용할 수 있도록 추천 결과 중 차량 전송용 payload만 리턴합니다.
    추천 이력은 서버에 저장되므로, 이후 경로안내 선택 학습은 chrstn_mno만 보내면 됩니다.
    """
    service = RecommendationService(db)
    recommendations = await service.get_personalized_recommendations(request)
    return [recommendation.delivery_payload for recommendation in recommendations]


@router.post(
    "/path-range/stations",
    response_model=PathRangeStationSearchResponse,
)
async def search_path_range_stations(
    request: PathRangeStationSearchRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    출발지와 목적지 사이의 실제 경로 거리로 만들어지는 경유 가능 범위에서
    충전소 후보를 조회합니다.
    """
    try:
        return await find_charging_stations(
            db,
            x_lat=float(request.start_latitude),
            x_lng=float(request.start_longitude),
            y_lat=float(request.destination_latitude),
            y_lng=float(request.destination_longitude),
            actual_distance_km=float(request.actual_distance_km),
            padding_km=float(request.padding_km),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
