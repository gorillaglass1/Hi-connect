from datetime import time

from pydantic import BaseModel, ConfigDict, Field


class HydrogenStationCreate(BaseModel):
    name: str
    address: str
    latitude: float
    longitude: float
    contact_number: str | None = Field(default=None)
    start_time: time | None = Field(default=None)
    end_time: time | None = Field(default=None)
    total_chargers: int = Field(default=0)
    payment_supported: str | None = Field(default=None)


class HydrogenStationUpdate(BaseModel):
    name: str | None = Field(default=None)
    address: str | None = Field(default=None)
    latitude: float | None = Field(default=None)
    longitude: float | None = Field(default=None)
    contact_number: str | None = Field(default=None)
    start_time: time | None = Field(default=None)
    end_time: time | None = Field(default=None)
    total_chargers: int | None = Field(default=None)
    payment_supported: str | None = Field(default=None)


class HydrogenStationResponse(HydrogenStationCreate):
    hydrogen_station_id: int

    model_config = ConfigDict(from_attributes=True)
