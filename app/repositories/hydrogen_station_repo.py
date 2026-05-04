from datetime import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hydrogen_station import hydrogen_station


async def create_hydrogen_station(
    db: AsyncSession,
    name: str,
    address: str,
    latitude: float,
    longitude: float,
    contact_number: str | None = None,
    start_time: time | None = None,
    end_time: time | None = None,
    total_chargers: int = 0,
    payment_supported: str | None = None,
):
    row = hydrogen_station(
        name=name,
        address=address,
        latitude=latitude,
        longitude=longitude,
        contact_number=contact_number,
        start_time=start_time,
        end_time=end_time,
        total_chargers=total_chargers,
        payment_supported=payment_supported,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def get_hydrogen_stations(
    db: AsyncSession,
    hydrogen_station_id: int | None = None,
    name: str | None = None,
    address: str | None = None,
    payment_supported: str | None = None,
    limit: int = 100,
    offset: int = 0,
):
    query = select(hydrogen_station)

    if hydrogen_station_id is not None:
        query = query.where(
            hydrogen_station.hydrogen_station_id == hydrogen_station_id
        )
    if name is not None:
        query = query.where(hydrogen_station.name == name)
    if address is not None:
        query = query.where(hydrogen_station.address == address)
    if payment_supported is not None:
        query = query.where(
            hydrogen_station.payment_supported == payment_supported
        )

    query = query.order_by(hydrogen_station.hydrogen_station_id.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()


async def update_hydrogen_station(
    db: AsyncSession,
    hydrogen_station_id: int,
    name: str | None = None,
    address: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    contact_number: str | None = None,
    start_time: time | None = None,
    end_time: time | None = None,
    total_chargers: int | None = None,
    payment_supported: str | None = None,
):
    result = await db.execute(
        select(hydrogen_station).where(
            hydrogen_station.hydrogen_station_id == hydrogen_station_id
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        return None

    if name is not None:
        row.name = name
    if address is not None:
        row.address = address
    if latitude is not None:
        row.latitude = latitude
    if longitude is not None:
        row.longitude = longitude
    if contact_number is not None:
        row.contact_number = contact_number
    if start_time is not None:
        row.start_time = start_time
    if end_time is not None:
        row.end_time = end_time
    if total_chargers is not None:
        row.total_chargers = total_chargers
    if payment_supported is not None:
        row.payment_supported = payment_supported

    await db.commit()
    await db.refresh(row)
    return row
