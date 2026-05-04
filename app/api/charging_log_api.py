from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.charging_log_schemas import ChargingLogCreate, ChargingLogResponse
from app.services.charging_log_service import ChargingLogService

router = APIRouter(prefix="/charging-logs", tags=["charging-logs"])


@router.post("", response_model=ChargingLogResponse, status_code=201)
async def create_charging_log(payload: ChargingLogCreate, db: AsyncSession = Depends(get_db)):
    return await ChargingLogService(db).create_charging_log(payload)


@router.get("", response_model=list[ChargingLogResponse])
async def list_charging_logs(
    charging_log_id: int | None = None,
    user_id: int | None = None,
    hydrogen_station_id: int | None = None,
    vehicle_id: int | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    return await ChargingLogService(db).get_charging_logs(
        charging_log_id,
        user_id,
        hydrogen_station_id,
        vehicle_id,
        limit,
        offset,
    )
