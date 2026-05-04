from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hydrogen_charger import hydrogen_charger


async def create_hydrogen_charger(
    db: AsyncSession,
    hydrogen_station_id: int,
    charger_status: str,
    pressure_type: str,
    charger_type: str | None = None,
    hydrogen_pressure_bar: int | None = None,
    restock_schedule: datetime | None = None,
):
    row = hydrogen_charger(
        hydrogen_station_id=hydrogen_station_id,
        charger_status=charger_status,
        charger_type=charger_type,
        hydrogen_pressure_bar=hydrogen_pressure_bar,
        pressure_type=pressure_type,
        restock_schedule=restock_schedule,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def get_hydrogen_chargers(
    db: AsyncSession,
    hydrogen_charger_id: int | None = None,
    hydrogen_station_id: int | None = None,
    charger_status: str | None = None,
    pressure_type: str | None = None,
    limit: int = 100,
    offset: int = 0,
):
    query = select(hydrogen_charger)

    if hydrogen_charger_id is not None:
        query = query.where(
            hydrogen_charger.hydrogen_charger_id == hydrogen_charger_id
        )
    if hydrogen_station_id is not None:
        query = query.where(
            hydrogen_charger.hydrogen_station_id == hydrogen_station_id
        )
    if charger_status is not None:
        query = query.where(hydrogen_charger.charger_status == charger_status)
    if pressure_type is not None:
        query = query.where(hydrogen_charger.pressure_type == pressure_type)

    query = query.order_by(hydrogen_charger.hydrogen_charger_id.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()
