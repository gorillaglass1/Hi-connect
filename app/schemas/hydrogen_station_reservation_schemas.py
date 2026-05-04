from datetime import datetime

from pydantic import BaseModel, ConfigDict


class HydrogenStationReservationCreate(BaseModel):
    hydrogen_charger_id: int
    hydrogen_station_id: int
    reservation_status: str
    user_id: int
    reservation_time: datetime
    expire_time: datetime


class HydrogenStationReservationResponse(HydrogenStationReservationCreate):
    hydrogen_station_reservation_id: int
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
