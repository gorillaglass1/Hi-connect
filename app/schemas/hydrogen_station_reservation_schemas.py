from datetime import datetime

from pydantic import BaseModel, ConfigDict


class Create_hydrogen_station_reservation(BaseModel):
    hydrogen_charger_id: int
    hydrogen_station_id: int
    reservation_status: str
    user_id: int
    reservation_time: datetime
    expire_time: datetime


class hydrogen_station_reservation_Response(Create_hydrogen_station_reservation):
    hydrogen_station_reservation_id: int
    updated_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)
