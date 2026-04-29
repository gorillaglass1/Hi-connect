from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hydrogen_station_realtime import HydrogenStationRealtime


async def upsert_station_realtime(
    db: AsyncSession,
    hydrogen_station_id: int,
    queue_count: int,
    avg_wait_time: int,
    station_status: str,
):
    result = await db.execute(
        select(HydrogenStationRealtime).where(
            HydrogenStationRealtime.hydrogen_station_id == hydrogen_station_id
        )
    )
    row = result.scalars().first()

    if row is None:
        row = HydrogenStationRealtime(
            hydrogen_station_id=hydrogen_station_id,
            queue_count=queue_count,
            avg_wait_time=avg_wait_time,
            station_status=station_status,
        )
        db.add(row)
    else:
        row.queue_count = queue_count
        row.avg_wait_time = avg_wait_time
        row.station_status = station_status

    await db.commit()
    await db.refresh(row)
    return row


async def get_station_realtime(
    db: AsyncSession,
    realtime_id: int | None = None,
    hydrogen_station_id: int | None = None,
    station_status: str | None = None,
    updated_from: datetime | None = None,
    updated_to: datetime | None = None,
    limit: int = 100,
    offset: int = 0,
):
    query = select(HydrogenStationRealtime)

    if realtime_id is not None:
        query = query.where(HydrogenStationRealtime.realtime_id == realtime_id)

    if hydrogen_station_id is not None:
        query = query.where(HydrogenStationRealtime.hydrogen_station_id == hydrogen_station_id)

    if station_status:
        query = query.where(HydrogenStationRealtime.station_status == station_status)

    if updated_from:
        query = query.where(HydrogenStationRealtime.updated_at >= updated_from)

    if updated_to:
        query = query.where(HydrogenStationRealtime.updated_at <= updated_to)

    query = query.order_by(HydrogenStationRealtime.updated_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()
