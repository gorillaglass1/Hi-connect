from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.charging_log import ChargingLog


async def create_charging_log(db: AsyncSession,
                                user_id: int, hydrogen_station_id: int,
                                vehicle_id: int, start_time: datetime,
                                end_time: datetime, charged_amount: float,
                                charging_cost: float, waiting_time: int,
                                ):
    charging_log = ChargingLog(user_id=user_id, hydrogen_station_id=hydrogen_station_id,
                               vehicle_id=vehicle_id, start_time=start_time, end_time=end_time,
                               charged_amount=charged_amount, charging_cost=charging_cost,
                               waiting_time=waiting_time)
    db.add(charging_log)
    await db.commit()
    await db.refresh(charging_log)
    return charging_log


async def get_charging_log_by_id(db: AsyncSession, log_id: int):
    result = await db.execute(select(ChargingLog).where(ChargingLog.id == log_id))
    return result.scalars().first()


async def get_charging_logs(
    db: AsyncSession,
    user_id: int | None = None,
    vehicle_id: int | None = None,
    hydrogen_station_id: int | None = None,
    start_from: datetime | None = None,
    end_to: datetime | None = None,
    limit: int = 100,
    offset: int = 0,
):
    query = select(ChargingLog)

    if user_id is not None:
        query = query.where(ChargingLog.user_id == user_id)

    if vehicle_id is not None:
        query = query.where(ChargingLog.vehicle_id == vehicle_id)

    if hydrogen_station_id is not None:
        query = query.where(ChargingLog.hydrogen_station_id == hydrogen_station_id)

    if start_from:
        query = query.where(ChargingLog.start_time >= start_from)

    if end_to:
        query = query.where(ChargingLog.end_time <= end_to)

    query = query.order_by(ChargingLog.start_time.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()
