from datetime import datetime

from pydantic import BaseModel, ConfigDict


class HydrogenChargerCreate(BaseModel):
    hydrogen_station_id: int
    charger_status: str
    charger_type: str | None = None
    hydrogen_pressure_bar: int | None = None
    pressure_type: str
    restock_schedule: datetime | None = None


class HydrogenChargerResponse(HydrogenChargerCreate):
    hydrogen_charger_id: int

    model_config = ConfigDict(from_attributes=True)
