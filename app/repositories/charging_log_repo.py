from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.charging_log import ChargingLog


async def create_charging_log(
    db: AsyncSession,
    user_id: int,
    hydrogen_station_id: int,
    vehicle_id: int,
    start_time: datetime,
    end_time: datetime,
    charged_amount: float | None = None,
    charging_cost: float | None = None,
    waiting_time: int | None = None,
):
    row = ChargingLog(
        user_id=user_id,
        hydrogen_station_id=hydrogen_station_id,
        vehicle_id=vehicle_id,
        start_time=start_time,
        end_time=end_time,
        charged_amount=charged_amount,
        charging_cost=charging_cost,
        waiting_time=waiting_time,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def get_charging_log_by_id(db: AsyncSession, charging_log_id: int):
    result = await db.execute(
        select(ChargingLog).where(ChargingLog.charging_log_id == charging_log_id)
    )
    return result.scalar_one_or_none()


async def get_charging_logs(
    db: AsyncSession,
    charging_log_id: int | None = None,
    user_id: int | None = None,
    hydrogen_station_id: int | None = None,
    vehicle_id: int | None = None,
    limit: int = 100,
    offset: int = 0,
):
    query = select(ChargingLog)

    if charging_log_id is not None:
        query = query.where(ChargingLog.charging_log_id == charging_log_id)
    if user_id is not None:
        query = query.where(ChargingLog.user_id == user_id)
    if hydrogen_station_id is not None:
        query = query.where(ChargingLog.hydrogen_station_id == hydrogen_station_id)
    if vehicle_id is not None:
        query = query.where(ChargingLog.vehicle_id == vehicle_id)

    query = query.order_by(ChargingLog.start_time.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()
