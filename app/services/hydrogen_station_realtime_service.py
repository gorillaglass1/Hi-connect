from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import hydrogen_station_realtime_repo
from app.schemas.hydrogen_station_realtime_schemas import HydrogenStationRealtimeCreate


class HydrogenStationRealtimeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def upsert_station_realtime(self, payload: HydrogenStationRealtimeCreate):
        return await hydrogen_station_realtime_repo.upsert_station_realtime(
            self.db,
            hydrogen_station_id=payload.hydrogen_station_id,
            available_chargers=payload.available_chargers,
            in_use_chargers=payload.in_use_chargers,
            queue_count=payload.queue_count,
            avg_wait_time=payload.avg_wait_time,
            hydrogen_stock_kg=payload.hydrogen_stock_kg,
            station_status=payload.station_status,
            last_restock_at=payload.last_restock_at,
            next_restock_schedule=payload.next_restock_schedule,
            utilization_rate=payload.utilization_rate,
        )

    async def get_station_realtime(
        self,
        realtime_id: int | None = None,
        hydrogen_station_id: int | None = None,
        station_status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ):
        return await hydrogen_station_realtime_repo.get_station_realtime(
            self.db,
            realtime_id=realtime_id,
            hydrogen_station_id=hydrogen_station_id,
            station_status=station_status,
            limit=limit,
            offset=offset,
        )
