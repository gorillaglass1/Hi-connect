from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import hydrogen_station_repo
from app.schemas.hydrogen_station_schema import HydrogenStationCreate


class HydrogenStationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_station(self, payload: HydrogenStationCreate):
        if payload.total_chargers < 0:
            raise HTTPException(status_code=400, detail="total_chargers must be >= 0")

        return await hydrogen_station_repo.create_hydrogen_station(
            self.db,
            name=payload.name,
            address=payload.address,
            latitude=payload.latitude,
            longitude=payload.longitude,
            contact_number=payload.contact_number,
            start_time=payload.start_time,
            end_time=payload.end_time,
            total_chargers=payload.total_chargers,
            payment_supported=payload.payment_supported,
        )

    async def get_station_by_id(self, hydrogen_station_id: int):
        rows = await hydrogen_station_repo.get_hydrogen_stations(
            self.db,
            hydrogen_station_id=hydrogen_station_id,
            limit=1,
        )
        if not rows:
            raise HTTPException(status_code=404, detail="Hydrogen station not found")
        return rows[0]

    async def get_stations(
        self,
        hydrogen_station_id: int | None = None,
        name: str | None = None,
        address: str | None = None,
        payment_supported: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ):
        return await hydrogen_station_repo.get_hydrogen_stations(
            self.db,
            hydrogen_station_id=hydrogen_station_id,
            name=name,
            address=address,
            payment_supported=payment_supported,
            limit=limit,
            offset=offset,
        )
