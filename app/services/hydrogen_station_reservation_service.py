from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import hydrogen_station_reservation_repo
from app.schemas.hydrogen_station_reservation_schemas import (
    HydrogenStationReservationCreate,
    HydrogenStationReservationUpdate,
)


class HydrogenStationReservationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_reservation(self, payload: HydrogenStationReservationCreate):
        if payload.expire_time <= payload.reservation_time:
            raise HTTPException(status_code=400, detail="expire_time must be after reservation_time")

        return await hydrogen_station_reservation_repo.create_reservation(
            self.db,
            hydrogen_charger_id=payload.hydrogen_charger_id,
            hydrogen_station_id=payload.hydrogen_station_id,
            user_id=payload.user_id,
            reservation_time=payload.reservation_time,
            expire_time=payload.expire_time,
        )

    async def get_reservations(
        self,
        hydrogen_station_reservation_id: int | None = None,
        hydrogen_charger_id: int | None = None,
        hydrogen_station_id: int | None = None,
        user_id: int | None = None,
        reservation_status: str | None = None,
        reservation_time=None,
        expire_time=None,
        limit: int = 100,
        offset: int = 0,
    ):
        return await hydrogen_station_reservation_repo.get_reservations(
            self.db,
            hydrogen_station_reservation_id=hydrogen_station_reservation_id,
            hydrogen_charger_id=hydrogen_charger_id,
            hydrogen_station_id=hydrogen_station_id,
            user_id=user_id,
            reservation_status=reservation_status,
            reservation_time=reservation_time,
            expire_time=expire_time,
            limit=limit,
            offset=offset,
        )

    async def update_reservation(
        self,
        hydrogen_station_reservation_id: int,
        payload: HydrogenStationReservationUpdate,
    ):
        reservation_time = payload.reservation_time
        expire_time = payload.expire_time
        if reservation_time is not None and expire_time is not None and expire_time <= reservation_time:
            raise HTTPException(status_code=400, detail="expire_time must be after reservation_time")

        row = await hydrogen_station_reservation_repo.update_reservation(
            self.db,
            hydrogen_station_reservation_id=hydrogen_station_reservation_id,
            hydrogen_charger_id=payload.hydrogen_charger_id,
            hydrogen_station_id=payload.hydrogen_station_id,
            reservation_status=payload.reservation_status,
            user_id=payload.user_id,
            reservation_time=reservation_time,
            expire_time=expire_time,
        )
        if row is None:
            raise HTTPException(status_code=404, detail="Reservation not found")
        return row
