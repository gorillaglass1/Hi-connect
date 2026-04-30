from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hydrogen_station_reservation import HydrogenStationReservation


async def create_reservation(
    db: AsyncSession,
    hydrogen_charger_id: int,
    hydrogen_station_id: int,
    user_id: int,
    reservation_time: datetime,
    expire_time: datetime,
):
    row = HydrogenStationReservation(
        hydrogen_charger_id=hydrogen_charger_id,
        hydrogen_station_id=hydrogen_station_id,
        reservation_status="RESERVED",
        user_id=user_id,
        reservation_time=reservation_time,
        expire_time=expire_time,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def get_reservations(
    db: AsyncSession,
    hydrogen_station_reservation_id: int | None,
    hydrogen_charger_id: int | None,
    hydrogen_station_id: int | None,
    user_id: int | None,
    reservation_status: str | None,
    reservation_time: datetime | None,
    expire_time: datetime | None,
    limit: int = 100,
    offset: int = 0,
):
    query = select(HydrogenStationReservation)

    if hydrogen_station_reservation_id is not None:
        query = query.where(
            HydrogenStationReservation.hydrogen_station_reservation_id
            == hydrogen_station_reservation_id
        )

    if hydrogen_charger_id is not None:
        query = query.where(
            HydrogenStationReservation.hydrogen_charger_id == hydrogen_charger_id
        )

    if hydrogen_station_id is not None:
        query = query.where(
            HydrogenStationReservation.hydrogen_station_id == hydrogen_station_id
        )

    if user_id is not None:
        query = query.where(HydrogenStationReservation.user_id == user_id)

    if reservation_status is not None:
        query = query.where(
            HydrogenStationReservation.reservation_status == reservation_status
        )

    if reservation_time is not None:
        query = query.where(
            HydrogenStationReservation.reservation_time == reservation_time
        )

    if expire_time is not None:
        query = query.where(
            HydrogenStationReservation.expire_time == expire_time
        )


    query = (
        query.order_by(HydrogenStationReservation.reservation_time.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(query)
    return result.scalars().all()
