from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.path_range_schema import (
    PathRangeStationSearchRequest,
    PathRangeStationSearchResponse,
)
from app.schemas.recommendation_schema import (
    HydrogenStationCard,
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
    자연어 쿼리(nl_query)가 포함된 경우 규칙 기반 후보 필터링을 거칩니다.
    충전소별 추천 사유 메시지는 Gemini API로 생성하며, 키가 없거나 호출이
    실패하면 규칙 기반 문구로 폴백합니다.
    """
    service = RecommendationService(db)
    return await service.get_personalized_recommendations(request)


@router.post(
    "/personalized/delivery-payloads",
    response_model=list[HydrogenStationCard],
)
async def search_personalized_recommendation_delivery_payloads(
    request: RecommendationSearchRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    차량/앱 충전소 카드 화면에서 사용할 수 있도록 추천 결과를 카드 형식으로 리턴합니다.
    추천 이력은 서버에 저장되므로, 이후 경로안내 선택 학습은 chrstn_mno(id)만 보내면 됩니다.
    isRecommended는 점수가 가장 높은 최상위 추천 1개에만 true로 설정됩니다.
    """
    service = RecommendationService(db)
    recommendations = await service.get_personalized_recommendations(request)
    return [
        HydrogenStationCard(
            id=recommendation.delivery_payload.chrstn_mno,
            name=recommendation.delivery_payload.chrstn_nm,
            address=recommendation.delivery_payload.road_nm_addr,
            status=recommendation.delivery_payload.oper_sttus_nm,
            pressure_info=recommendation.delivery_payload.pressure_info,
            distance_km=recommendation.distance_to_station,
            wait_minutes=recommendation.wait_time_minutes,
            is_recommended=(index == 0),
            latitude=recommendation.delivery_payload.latitude,
            longitude=recommendation.delivery_payload.longitude,
        )
        for index, recommendation in enumerate(recommendations)
    ]


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
