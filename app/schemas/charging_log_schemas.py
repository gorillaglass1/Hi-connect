from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ChargingLogCreate(BaseModel):
    user_id: int
    hydrogen_station_id: int
    vehicle_id: int
    start_time: datetime
    end_time: datetime
    charged_amount: float | None = None
    charging_cost: float | None = None
    waiting_time: int | None = None


class ChargingLogResponse(ChargingLogCreate):
    charging_log_id: int
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
