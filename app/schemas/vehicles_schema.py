from datetime import datetime

from pydantic import BaseModel, ConfigDict


class VehicleCreate(BaseModel):
    user_id: int
    vehicle_number: str
    model: str
    vehicle_type: str
    fuel_type: str = "hydrogen"
    tank_capacity: float
    avg_efficiency: float | None = None


class VehicleResponse(VehicleCreate):
    vehicle_id: int
    registered_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
