from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import hydrogen_charger_repo
from app.schemas.hydrogen_charger_schema import HydrogenChargerCreate, HydrogenChargerUpdate


class HydrogenChargerService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_charger(self, payload: HydrogenChargerCreate):
        if payload.hydrogen_pressure_bar is not None and payload.hydrogen_pressure_bar < 0:
            raise HTTPException(status_code=400, detail="hydrogen_pressure_bar must be >= 0")

        return await hydrogen_charger_repo.create_hydrogen_charger(
            self.db,
            hydrogen_station_id=payload.hydrogen_station_id,
            charger_status=payload.charger_status,
            pressure_type=payload.pressure_type,
            charger_type=payload.charger_type,
            hydrogen_pressure_bar=payload.hydrogen_pressure_bar,
            restock_schedule=payload.restock_schedule,
        )

    async def get_chargers(
        self,
        hydrogen_charger_id: int | None = None,
        hydrogen_station_id: int | None = None,
        charger_status: str | None = None,
        pressure_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ):
        return await hydrogen_charger_repo.get_hydrogen_chargers(
            self.db,
            hydrogen_charger_id=hydrogen_charger_id,
            hydrogen_station_id=hydrogen_station_id,
            charger_status=charger_status,
            pressure_type=pressure_type,
            limit=limit,
            offset=offset,
        )

    async def update_charger(self, hydrogen_charger_id: int, payload: HydrogenChargerUpdate):
        if payload.hydrogen_pressure_bar is not None and payload.hydrogen_pressure_bar < 0:
            raise HTTPException(status_code=400, detail="hydrogen_pressure_bar must be >= 0")

        row = await hydrogen_charger_repo.update_hydrogen_charger(
            self.db,
            hydrogen_charger_id=hydrogen_charger_id,
            hydrogen_station_id=payload.hydrogen_station_id,
            charger_status=payload.charger_status,
            charger_type=payload.charger_type,
            hydrogen_pressure_bar=payload.hydrogen_pressure_bar,
            pressure_type=payload.pressure_type,
            restock_schedule=payload.restock_schedule,
        )
        if row is None:
            raise HTTPException(status_code=404, detail="Hydrogen charger not found")
        return row
