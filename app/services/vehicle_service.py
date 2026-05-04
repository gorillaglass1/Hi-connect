from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import vehicles_repo
from app.schemas.vehicles_schema import VehicleCreate


class VehicleService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_vehicle(self, payload: VehicleCreate):
        if payload.tank_capacity <= 0:
            raise HTTPException(status_code=400, detail="tank_capacity must be greater than 0")
        if payload.avg_efficiency is not None and payload.avg_efficiency <= 0:
            raise HTTPException(status_code=400, detail="avg_efficiency must be greater than 0")

        exists = await vehicles_repo.get_vehicles(
            self.db,
            vehicle_number=payload.vehicle_number,
            limit=1,
        )
        if exists:
            raise HTTPException(status_code=409, detail="Vehicle number already exists")

        try:
            return await vehicles_repo.create_vehicle(
                self.db,
                user_id=payload.user_id,
                vehicle_number=payload.vehicle_number,
                model=payload.model,
                vehicle_type=payload.vehicle_type,
                fuel_type=payload.fuel_type,
                tank_capacity=payload.tank_capacity,
                avg_efficiency=payload.avg_efficiency,
            )
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(status_code=409, detail="Vehicle create conflict")

    async def get_vehicle_by_id(self, vehicle_id: int):
        rows = await vehicles_repo.get_vehicles(self.db, vehicle_id=vehicle_id, limit=1)
        if not rows:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        return rows[0]

    async def get_vehicles(
        self,
        vehicle_id: int | None = None,
        user_id: int | None = None,
        vehicle_number: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ):
        return await vehicles_repo.get_vehicles(
            self.db,
            vehicle_id=vehicle_id,
            user_id=user_id,
            vehicle_number=vehicle_number,
            limit=limit,
            offset=offset,
        )
