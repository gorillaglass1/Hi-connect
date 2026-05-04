from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.hydrogen_station_realtime_schemas import (
    HydrogenStationRealtimeCreate,
    HydrogenStationRealtimeResponse,
)
from app.services.hydrogen_station_realtime_service import HydrogenStationRealtimeService

router = APIRouter(prefix="/hydrogen-station-realtime", tags=["hydrogen-station-realtime"])


@router.post("", response_model=HydrogenStationRealtimeResponse)
async def upsert_station_realtime(
    payload: HydrogenStationRealtimeCreate,
    db: AsyncSession = Depends(get_db),
):
    return await HydrogenStationRealtimeService(db).upsert_station_realtime(payload)


@router.get("", response_model=list[HydrogenStationRealtimeResponse])
async def list_station_realtime(
    realtime_id: int | None = None,
    hydrogen_station_id: int | None = None,
    station_status: str | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    return await HydrogenStationRealtimeService(db).get_station_realtime(
        realtime_id,
        hydrogen_station_id,
        station_status,
        limit,
        offset,
    )
