from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ChargingLogItemCreate(BaseModel):
    chrstn_mno: str
    start_time: datetime
    end_time: datetime
    charged_amount: Decimal | None = Field(default=None)
    charging_cost: Decimal | None = Field(default=None)
    waiting_time: int | None = Field(default=None)


class ChargingLogCreate(BaseModel):
    user_id: int
    vehicle_id: int
    logs: list[ChargingLogItemCreate] = Field(min_length=1)


class ChargingLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    charging_log_id: int
    user_id: int
    vehicle_id: int
    chrstn_mno: str
    start_time: datetime
    end_time: datetime
    charged_amount: Decimal | None = Field(default=None)
    charging_cost: Decimal | None = Field(default=None)
    waiting_time: int | None = Field(default=None)
    created_at: datetime | None = Field(default=None)
