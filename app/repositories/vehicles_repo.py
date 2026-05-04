from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vehicles import Vehicles


async def create_vehicle(
    db: AsyncSession,
    user_id: int,
    vehicle_number: str,
    model: str,
    vehicle_type: str,
    fuel_type: str = "hydrogen",
    tank_capacity: float = 0.0,
    avg_efficiency: float | None = None,
):
    row = Vehicles(
        user_id=user_id,
        vehicle_number=vehicle_number,
        model=model,
        vehicle_type=vehicle_type,
        fuel_type=fuel_type,
        tank_capacity=tank_capacity,
        avg_efficiency=avg_efficiency,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def get_vehicles(
    db: AsyncSession,
    vehicle_id: int | None = None,
    user_id: int | None = None,
    vehicle_number: str | None = None,
    limit: int = 100,
    offset: int = 0,
):
    query = select(Vehicles)

    if vehicle_id is not None:
        query = query.where(Vehicles.vehicle_id == vehicle_id)
    if user_id is not None:
        query = query.where(Vehicles.user_id == user_id)
    if vehicle_number is not None:
        query = query.where(Vehicles.vehicle_number == vehicle_number)

    query = query.order_by(Vehicles.vehicle_id.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()
