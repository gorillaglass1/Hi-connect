from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.hydrogen_station_reservation_schemas import (
    HydrogenStationReservationCreate,
    HydrogenStationReservationResponse,
    HydrogenStationReservationUpdate,
)
from app.services.hydrogen_station_reservation_service import (
    HydrogenStationReservationService,
)

router = APIRouter(prefix="/hydrogen-station-reservations", tags=["hydrogen-station-reservations"])


@router.post("", response_model=HydrogenStationReservationResponse, status_code=201)
async def create_reservation(
    payload: HydrogenStationReservationCreate,
    db: AsyncSession = Depends(get_db),
):
    return await HydrogenStationReservationService(db).create_reservation(payload)


@router.get("", response_model=list[HydrogenStationReservationResponse])
async def list_reservations(
    hydrogen_station_reservation_id: int | None = None,
    charger_id: int | None = None,
    hydrogen_charger_id: int | None = None,
    station_id: int | None = None,
    hydrogen_station_id: int | None = None,
    user_id: int | None = None,
    reservation_status: str | None = None,
    reservation_time: datetime | None = None,
    expire_time: datetime | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    return await HydrogenStationReservationService(db).get_reservations(
        hydrogen_station_reservation_id,
        charger_id or hydrogen_charger_id,
        station_id or hydrogen_station_id,
        user_id,
        reservation_status,
        reservation_time,
        expire_time,
        limit,
        offset,
    )


@router.patch(
    "/{hydrogen_station_reservation_id}",
    response_model=HydrogenStationReservationResponse,
)
async def update_reservation(
    hydrogen_station_reservation_id: int,
    payload: HydrogenStationReservationUpdate,
    db: AsyncSession = Depends(get_db),
):
    return await HydrogenStationReservationService(db).update_reservation(
        hydrogen_station_reservation_id,
        payload,
    )
