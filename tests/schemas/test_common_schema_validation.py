from datetime import datetime

import pytest
from pydantic import ValidationError

from app.schemas.charging_log_schema import ChargingLogCreate
from app.schemas.hydrogen_station_facilities_schema import (
    HydrogenStationAdditionalInfoCreate,
)
from app.schemas.hydrogen_station_status_schema import HydrogenStationStatusCreate
from app.schemas.recommendation_history_schema import RecommendationHistoryCreate


def test_charging_log_create_requires_at_least_one_log():
    with pytest.raises(ValidationError):
        ChargingLogCreate(user_id=1, logs=[])


def test_recommendation_history_create_requires_at_least_one_recommendation():
    with pytest.raises(ValidationError):
        RecommendationHistoryCreate(user_id=1, recommendations=[])


def test_hydrogen_station_status_parses_hying_datetime():
    payload = HydrogenStationStatusCreate(
        chrstn_mno="ST-001",
        last_mdfcn_dt="20260524123456",
    )

    assert payload.last_mdfcn_dt == datetime(2026, 5, 24, 12, 34, 56)


def test_hydrogen_station_status_treats_blank_datetime_as_none():
    payload = HydrogenStationStatusCreate(
        chrstn_mno="ST-001",
        last_mdfcn_dt="",
    )

    assert payload.last_mdfcn_dt is None


def test_hydrogen_station_facility_parses_space_timezone_timestamp():
    payload = HydrogenStationAdditionalInfoCreate(
        chrstn_mno="ST-001",
        timestamp="2022-01-19 01:32:24.340447 +00:00",
    )

    assert payload.timestamp == datetime(2022, 1, 19, 1, 32, 24, 340447)


def test_hydrogen_station_facility_parses_colon_microsecond_timestamp():
    payload = HydrogenStationAdditionalInfoCreate(
        chrstn_mno="ST-001",
        timestamp="2026-05-22 15:45:14:205554 +09:00",
    )

    assert payload.timestamp == datetime(2026, 5, 22, 15, 45, 14, 205554)
