from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import charging_log_repo
from app.schemas.charging_log_schemas import ChargingLogCreate


class ChargingLogService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_charging_log(self, payload: ChargingLogCreate):
        if payload.end_time <= payload.start_time:
            raise HTTPException(status_code=400, detail="end_time must be after start_time")
        if payload.charged_amount is not None and payload.charged_amount < 0:
            raise HTTPException(status_code=400, detail="charged_amount must be >= 0")
        if payload.charging_cost is not None and payload.charging_cost < 0:
            raise HTTPException(status_code=400, detail="charging_cost must be >= 0")
        if payload.waiting_time is not None and payload.waiting_time < 0:
            raise HTTPException(status_code=400, detail="waiting_time must be >= 0")

        return await charging_log_repo.create_charging_log(
            self.db,
            user_id=payload.user_id,
            hydrogen_station_id=payload.hydrogen_station_id,
            vehicle_id=payload.vehicle_id,
            start_time=payload.start_time,
            end_time=payload.end_time,
            charged_amount=payload.charged_amount,
            charging_cost=payload.charging_cost,
            waiting_time=payload.waiting_time,
        )

    async def get_charging_logs(
        self,
        charging_log_id: int | None = None,
        user_id: int | None = None,
        hydrogen_station_id: int | None = None,
        vehicle_id: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ):
        return await charging_log_repo.get_charging_logs(
            self.db,
            charging_log_id=charging_log_id,
            user_id=user_id,
            hydrogen_station_id=hydrogen_station_id,
            vehicle_id=vehicle_id,
            limit=limit,
            offset=offset,
        )
