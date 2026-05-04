from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hydrogen_station_realtime import HydrogenStationRealtime


async def upsert_station_realtime(
    db: AsyncSession,
    hydrogen_station_id: int,
    available_chargers: int | None = None,
    in_use_chargers: int | None = None,
    queue_count: int | None = None,
    avg_wait_time: int | None = None,
    hydrogen_stock_kg: float | None = None,
    station_status: str | None = None,
    last_restock_at=None,
    next_restock_schedule=None,
    utilization_rate: float | None = None,
):
    result = await db.execute(
        select(HydrogenStationRealtime).where(
            HydrogenStationRealtime.hydrogen_station_id == hydrogen_station_id
        )
    )
    row = result.scalar_one_or_none()

    if row is None:
        row = HydrogenStationRealtime(hydrogen_station_id=hydrogen_station_id)
        db.add(row)

    updates = {
        "available_chargers": available_chargers,
        "in_use_chargers": in_use_chargers,
        "queue_count": queue_count,
        "avg_wait_time": avg_wait_time,
        "hydrogen_stock_kg": hydrogen_stock_kg,
        "station_status": station_status,
        "last_restock_at": last_restock_at,
        "next_restock_schedule": next_restock_schedule,
        "utilization_rate": utilization_rate,
    }
    for field, value in updates.items():
        if value is not None:
            setattr(row, field, value)

    await db.commit()
    await db.refresh(row)
    return row


async def get_station_realtime(
    db: AsyncSession,
    realtime_id: int | None = None,
    hydrogen_station_id: int | None = None,
    station_status: str | None = None,
    limit: int = 100,
    offset: int = 0,
):
    query = select(HydrogenStationRealtime)

    if realtime_id is not None:
        query = query.where(HydrogenStationRealtime.realtime_id == realtime_id)
    if hydrogen_station_id is not None:
        query = query.where(
            HydrogenStationRealtime.hydrogen_station_id == hydrogen_station_id
        )
    if station_status is not None:
        query = query.where(HydrogenStationRealtime.station_status == station_status)

    query = query.order_by(HydrogenStationRealtime.updated_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()
