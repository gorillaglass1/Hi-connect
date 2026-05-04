from datetime import time

from pydantic import BaseModel, ConfigDict


class HydrogenStationCreate(BaseModel):
    name: str
    address: str
    latitude: float
    longitude: float
    contact_number: str | None = None
    start_time: time | None = None
    end_time: time | None = None
    total_chargers: int = 0
    payment_supported: str | None = None


class HydrogenStationUpdate(BaseModel):
    name: str | None = None
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    contact_number: str | None = None
    start_time: time | None = None
    end_time: time | None = None
    total_chargers: int | None = None
    payment_supported: str | None = None


class HydrogenStationResponse(HydrogenStationCreate):
    hydrogen_station_id: int

    model_config = ConfigDict(from_attributes=True)
