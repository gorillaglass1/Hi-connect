from datetime import datetime

from pydantic import BaseModel, ConfigDict


class HydrogenStationRealtimeCreate(BaseModel):
    hydrogen_station_id: int
    available_chargers: int = 0
    in_use_chargers: int = 0
    queue_count: int = 0
    avg_wait_time: int | None = None
    hydrogen_stock_kg: float | None = None
    station_status: str | None = None
    last_restock_at: datetime | None = None
    next_restock_schedule: datetime | None = None
    utilization_rate: float | None = None


class HydrogenStationRealtimeResponse(HydrogenStationRealtimeCreate):
    realtime_id: int
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
