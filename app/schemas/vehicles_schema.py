from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class VehicleCreate(BaseModel):
    user_id: int
    vehicle_number: str
    model: str
    vehicle_type: str
    fuel_type: str = Field(default="hydrogen")
    tank_capacity: float
    avg_efficiency: float | None = Field(default=None)


class VehicleUpdate(BaseModel):
    user_id: int | None = Field(default=None)
    vehicle_number: str | None = Field(default=None)
    model: str | None = Field(default=None)
    vehicle_type: str | None = Field(default=None)
    fuel_type: str | None = Field(default=None)
    tank_capacity: float | None = Field(default=None)
    avg_efficiency: float | None = Field(default=None)


class VehicleResponse(VehicleCreate):
    vehicle_id: int
    registered_at: datetime | None = Field(default=None)

    model_config = ConfigDict(from_attributes=True)
