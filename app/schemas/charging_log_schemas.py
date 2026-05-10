from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ChargingLogCreate(BaseModel):
    user_id: int
    hydrogen_station_id: int
    vehicle_id: int
    start_time: datetime
    end_time: datetime
    charged_amount: float | None = Field(default=None)
    charging_cost: float | None = Field(default=None)
    waiting_time: int | None = Field(default=None)


class ChargingLogResponse(ChargingLogCreate):
    charging_log_id: int
    created_at: datetime | None = Field(default=None)

    model_config = ConfigDict(from_attributes=True)
