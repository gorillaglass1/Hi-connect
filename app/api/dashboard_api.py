"""대시보드 통합 인사이트 API (단일 엔드포인트 + 단일 LLM 호출).

참고: GET /dashboard 는 index.py 에서 이미 HTML 페이지로 사용 중이므로,
데이터 API 는 /dashboard/insights 로 노출한다.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.dashboard_schema import DashboardResponse
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/insights", response_model=DashboardResponse)
async def get_dashboard_insights(
    lat: float = Query(..., ge=-90, le=90, description="현재 위도"),
    lon: float = Query(..., ge=-180, le=180, description="현재 경도"),
    distance_km: float = Query(..., ge=0, description="CO2 환산용 주행거리 (km)"),
    fuel_percent: float | None = Query(
        default=None, ge=0, le=100, description="현재 연료 잔량 (%) - 팁/캐시 구간용"
    ),
    db: AsyncSession = Depends(get_db),
):
    """대시보드에 필요한 모든 인사이트를 단일 응답으로 반환한다.

    condition / hydrogen_tip 은 LLM 결과(실패 시 null 또는 기본 팁),
    co2 / nearest_station 은 백엔드 계산으로 항상 채운다. LLM 실패/타임아웃에도
    500 으로 죽지 않는다.
    """
    return await DashboardService(db).get_dashboard(
        lat=lat,
        lon=lon,
        distance_km=distance_km,
        fuel_percent=fuel_percent,
    )
