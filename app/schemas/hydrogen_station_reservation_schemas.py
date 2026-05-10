from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class HydrogenStationReservationCreate(BaseModel):
    hydrogen_charger_id: int
    hydrogen_station_id: int
    reservation_status: str
    user_id: int
    reservation_time: datetime
    expire_time: datetime


class HydrogenStationReservationUpdate(BaseModel):
    hydrogen_charger_id: int | None = Field(default=None)
    hydrogen_station_id: int | None = Field(default=None)
    reservation_status: str | None = Field(default=None)
    user_id: int | None = Field(default=None)
    reservation_time: datetime | None = Field(default=None)
    expire_time: datetime | None = Field(default=None)


class HydrogenStationReservationResponse(HydrogenStationReservationCreate):
    hydrogen_station_reservation_id: int
    created_at: datetime | None = Field(default=None)

    model_config = ConfigDict(from_attributes=True)
