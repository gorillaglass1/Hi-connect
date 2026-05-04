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


async def update_vehicle(
    db: AsyncSession,
    vehicle_id: int,
    user_id: int | None = None,
    vehicle_number: str | None = None,
    model: str | None = None,
    vehicle_type: str | None = None,
    fuel_type: str | None = None,
    tank_capacity: float | None = None,
    avg_efficiency: float | None = None,
):
    result = await db.execute(select(Vehicles).where(Vehicles.vehicle_id == vehicle_id))
    row = result.scalar_one_or_none()
    if row is None:
        return None

    if user_id is not None:
        row.user_id = user_id
    if vehicle_number is not None:
        row.vehicle_number = vehicle_number
    if model is not None:
        row.model = model
    if vehicle_type is not None:
        row.vehicle_type = vehicle_type
    if fuel_type is not None:
        row.fuel_type = fuel_type
    if tank_capacity is not None:
        row.tank_capacity = tank_capacity
    if avg_efficiency is not None:
        row.avg_efficiency = avg_efficiency

    await db.commit()
    await db.refresh(row)
    return row
