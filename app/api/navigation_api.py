from datetime import datetime
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.hydrogen_stations import HydrogenStation
from app.models.recommendation_history import RecommendationHistory

router = APIRouter(prefix="/navigation", tags=["navigation"])


class PushWaypointRequest(BaseModel):
    user_id: int = Field(..., description="사용자 ID")
    chrstn_mno: str = Field(..., description="선택된 경유 수소충전소 관리번호")
    destination_latitude: Decimal = Field(..., description="최종 목적지 위도")
    destination_longitude: Decimal = Field(..., description="최종 목적지 경도")


class WaypointData(BaseModel):
    name: str
    lat: float
    lon: float


class DestinationData(BaseModel):
    lat: float
    lon: float


class TelematicsPayload(BaseModel):
    vehicle_id: str
    command: str
    data: dict
    sent_at: str


class PushWaypointResponse(BaseModel):
    status: str
    message: str
    telematics_payload: TelematicsPayload
    deeplink_url: str


@router.post("/push-waypoint", response_model=PushWaypointResponse)
async def push_waypoint(
    payload: PushWaypointRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    현대자동차 블루링크/Kia Connect API 및 내비게이션 딥링크를 시뮬레이션하여 
    차량 내비게이션에 경유지 추가 명령을 전송하고, DB 히스토리를 업데이트합니다.
    """
    # 1. Verify hydrogen station exists
    stmt = select(HydrogenStation).where(HydrogenStation.chrstn_mno == payload.chrstn_mno)
    result = await db.execute(stmt)
    station = result.scalar_one_or_none()
    
    if not station:
        raise HTTPException(
            status_code=404,
            detail=f"Hydrogen station with ID {payload.chrstn_mno} not found.",
        )

    # 2. Update recommendation_history selected status
    # Find the most recent recommendation history entry for this user and station
    hist_stmt = (
        select(RecommendationHistory)
        .where(RecommendationHistory.user_id == payload.user_id)
        .where(RecommendationHistory.chrstn_mno == payload.chrstn_mno)
        .order_by(RecommendationHistory.recommendation_id.desc())
        .limit(1)
    )
    hist_result = await db.execute(hist_stmt)
    history_entry = hist_result.scalar_one_or_none()

    if history_entry:
        history_entry.selected = True
        history_entry.selected_at = datetime.now()
        await db.commit()
        await db.refresh(history_entry)

    # 3. Build simulated response payload
    st_lat = float(station.let) if station.let else 0.0
    st_lon = float(station.lon) if station.lon else 0.0
    dest_lat = float(payload.destination_latitude)
    dest_lon = float(payload.destination_longitude)

    telematics = TelematicsPayload(
        vehicle_id="SIMULATED-NEXO-EV-7777",
        command="CCS_ADD_WAYPOINT",
        data={
            "waypoint": {
                "name": station.chrstn_nm,
                "lat": st_lat,
                "lon": st_lon,
            },
            "destination": {
                "lat": dest_lat,
                "lon": dest_lon,
            }
        },
        sent_at=datetime.utcnow().isoformat() + "Z"
    )

    deeplink = (
        f"hyundainav://route?dest_lat={dest_lat}&dest_lon={dest_lon}"
        f"&waypoint1_lat={st_lat}&waypoint1_lon={st_lon}"
        f"&waypoint1_name={station.chrstn_nm}&user_id={payload.user_id}"
    )

    return PushWaypointResponse(
        status="SUCCESS",
        message="원격 경유지 전송 성공 (현대 BlueLink Connected Car Service 연동 성공)",
        telematics_payload=telematics,
        deeplink_url=deeplink,
    )
