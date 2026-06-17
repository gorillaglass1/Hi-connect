from fastapi import APIRouter, Query

from app.schemas.ex_highway_schema import (
    RealtimeTrafficResponse,
    RestAreaWeatherResponse,
)
from app.services.ex_highway_service import ExHighwayService

router = APIRouter(prefix="/highway", tags=["highway"])


@router.get(
    "/rest-areas/weather",
    response_model=RestAreaWeatherResponse,
    response_model_by_alias=False,
)
async def get_rest_area_weather(
    sdate: str = Query(..., description="조회 날짜 (예: 20260617)"),
    std_hour: str = Query(..., alias="stdHour", description="시간대 (예: 14)"),
    page_no: int | None = Query(default=None, ge=1, alias="pageNo", description="페이지 번호"),
    num_of_rows: int | None = Query(
        default=None, ge=1, le=1000, alias="numOfRows", description="페이지당 행 수"
    ),
):
    """한국도로공사 휴게소별 날씨 정보를 조회합니다."""
    extra_params: dict = {}
    if page_no is not None:
        extra_params["pageNo"] = page_no
    if num_of_rows is not None:
        extra_params["numOfRows"] = num_of_rows
    return await ExHighwayService().get_rest_area_weather(
        sdate, std_hour, extra_params or None
    )


@router.get(
    "/traffic/realtime",
    response_model=RealtimeTrafficResponse,
    response_model_by_alias=False,
)
async def get_realtime_traffic(
    page_no: int | None = Query(default=None, ge=1, alias="pageNo", description="페이지 번호"),
    num_of_rows: int | None = Query(
        default=None, ge=1, le=1000, alias="numOfRows", description="페이지당 행 수"
    ),
):
    """한국도로공사 실시간 교통량을 조회합니다."""
    extra_params: dict = {}
    if page_no is not None:
        extra_params["pageNo"] = page_no
    if num_of_rows is not None:
        extra_params["numOfRows"] = num_of_rows
    return await ExHighwayService().get_realtime_traffic(extra_params or None)
