from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class HydrogenChargerCreate(BaseModel):
    hydrogen_station_id: int
    charger_status: str
    charger_type: str | None = Field(default=None)
    hydrogen_pressure_bar: int | None = Field(default=None)
    pressure_type: str
    restock_schedule: datetime | None = Field(default=None)


class HydrogenChargerUpdate(BaseModel):
    hydrogen_station_id: int | None = Field(default=None)
    charger_status: str | None = Field(default=None)
    charger_type: str | None = Field(default=None)
    hydrogen_pressure_bar: int | None = Field(default=None)
    pressure_type: str | None = Field(default=None)
    restock_schedule: datetime | None = Field(default=None)


class HydrogenChargerResponse(HydrogenChargerCreate):
    hydrogen_charger_id: int

    model_config = ConfigDict(from_attributes=True)
