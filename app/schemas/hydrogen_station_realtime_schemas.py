from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class HydrogenStationRealtimeCreate(BaseModel):
    hydrogen_station_id: int
    available_chargers: int = Field(default=0)
    in_use_chargers: int = Field(default=0)
    queue_count: int = Field(default=0)
    avg_wait_time: int | None = Field(default=None)
    hydrogen_stock_kg: float | None = Field(default=None)
    station_status: str | None = Field(default=None)
    last_restock_at: datetime | None = Field(default=None)
    next_restock_schedule: datetime | None = Field(default=None)
    utilization_rate: float | None = Field(default=None)


class HydrogenStationRealtimeResponse(HydrogenStationRealtimeCreate):
    realtime_id: int
    updated_at: datetime | None = Field(default=None)

    model_config = ConfigDict(from_attributes=True)
