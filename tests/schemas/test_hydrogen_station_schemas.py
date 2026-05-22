from datetime import time

from app.schemas.hydrogen_station_facilities import (
    HydrogenStationAdditionalInfoCreate,
)
from app.schemas.hydrogen_stations_schemas import HydrogenStationCreate


def test_hydrogen_station_accepts_24_hour_close_time():
    payload = HydrogenStationCreate.model_validate(
        {
            "chrstn_mno": "ST-24",
            "chrstn_nm": "24 Hour Station",
            "useehr_hr_mon": "24:00",
        }
    )

    assert payload.useehr_hr_mon == time(23, 59, 59)


def test_hydrogen_station_facility_accepts_colon_microsecond_timestamp():
    payload = HydrogenStationAdditionalInfoCreate.model_validate(
        {
            "chrstn_mno": "ST-FAC",
            "timestamp": "2026-05-22 15:45:14:205554 +09:00",
        }
    )

    assert payload.timestamp.year == 2026
    assert payload.timestamp.microsecond == 205554
