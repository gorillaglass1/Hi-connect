from datetime import datetime, time
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.charging_log_schema import ChargingLogCreate, ChargingLogItemCreate
from app.schemas.hydrogen_station_facilities_schema import (
    HydrogenStationAdditionalInfoCreate,
)
from app.schemas.hydrogen_station_schema import HydrogenStationCreate
from app.schemas.hydrogen_station_status_schema import HydrogenStationStatusCreate
from app.schemas.recommendation_history_schema import (
    RecommendationHistoryCreate,
    RecommendationStationCreate,
)
from app.schemas.recommendation_schema import (
    RecommendationDeliveryPayload,
    RecommendationSearchRequest,
    RecommendedStationResponse,
    SubScores,
)
from app.schemas.user_preference_schema import (
    UserCreate,
    UserPreferenceLearningRequest,
    UserPreferenceUpdate,
)


def test_charging_log_create_requires_at_least_one_log():
    with pytest.raises(ValidationError):
        ChargingLogCreate(user_id=1, logs=[])


def test_charging_log_item_preserves_decimal_values():
    item = ChargingLogItemCreate(
        chrstn_mno="SCHEMA-CHARGE-001",
        start_time="2026-05-24T09:00:00",
        end_time="2026-05-24T09:30:00",
        charged_amount="2.35",
        charging_cost="21000.50",
        waiting_time=7,
    )

    assert item.start_time == datetime(2026, 5, 24, 9, 0)
    assert item.charged_amount == Decimal("2.35")
    assert item.charging_cost == Decimal("21000.50")


def test_hydrogen_station_create_normalizes_24_hour_time_and_empty_dates():
    station = HydrogenStationCreate(
        chrstn_mno="SCHEMA-ST-001",
        chrstn_nm="스키마 충전소",
        usebhr_hr_mon="24:00",
        useehr_hr_mon="",
        rest_bgng_hr=None,
        last_mdfcn_dt="",
        timestamp="",
    )

    assert station.usebhr_hr_mon == time(23, 59, 59)
    assert station.useehr_hr_mon is None
    assert station.rest_bgng_hr is None
    assert station.last_mdfcn_dt is None
    assert station.timestamp is None


def test_hydrogen_station_create_parses_hying_timestamps():
    station = HydrogenStationCreate(
        chrstn_mno="SCHEMA-ST-002",
        chrstn_nm="시간 파싱 충전소",
        last_mdfcn_dt="20260524123456",
        timestamp="2026-05-24 12:34:56:123456 +09:00",
    )

    assert station.last_mdfcn_dt == datetime(2026, 5, 24, 12, 34, 56)
    assert station.timestamp == datetime(2026, 5, 24, 12, 34, 56, 123456)


def test_hydrogen_station_status_create_parses_last_modified_time():
    status = HydrogenStationStatusCreate(
        chrstn_mno="SCHEMA-ST-003",
        wait_vhcle_alge=2,
        last_mdfcn_dt="20260524010203",
    )

    assert status.wait_vhcle_alge == 2
    assert status.last_mdfcn_dt == datetime(2026, 5, 24, 1, 2, 3)


def test_hydrogen_station_facility_create_parses_timestamp_variants():
    facility = HydrogenStationAdditionalInfoCreate(
        chrstn_mno="SCHEMA-ST-004",
        adi_info_se_cd="CVS",
        adi_info_se_nm="편의점",
        last_mdfcn_dt="20260524010203",
        timestamp="2026-05-24 01:02:03.123456 +00:00",
    )

    assert facility.last_mdfcn_dt == datetime(2026, 5, 24, 1, 2, 3)
    assert facility.timestamp == datetime(2026, 5, 24, 1, 2, 3, 123456)


def test_recommendation_history_create_requires_recommendations():
    with pytest.raises(ValidationError):
        RecommendationHistoryCreate(user_id=1, recommendations=[])


def test_recommendation_history_station_defaults_to_unselected():
    station = RecommendationStationCreate(
        chrstn_mno="SCHEMA-REC-001",
        recommendation_score="88.25",
    )

    assert station.recommendation_score == Decimal("88.25")
    assert station.selected is False
    assert station.selected_at is None


def test_recommendation_search_request_defaults_and_decimal_inputs():
    request = RecommendationSearchRequest(
        user_id=1,
        current_latitude="37.405",
        current_longitude="126.721",
        destination_latitude="37.460",
        destination_longitude="126.450",
        remaining_range="45.0",
    )

    assert request.current_latitude == Decimal("37.405")
    assert request.nl_query is None


def test_recommendation_search_request_rejects_client_alpha_inputs():
    with pytest.raises(ValidationError):
        RecommendationSearchRequest(
            user_id=1,
            current_latitude="37.405",
            current_longitude="126.721",
            destination_latitude="37.460",
            destination_longitude="126.450",
            remaining_range="45.0",
            alpha="15.0",
        )


def test_recommendation_search_request_rejects_client_path_range_inputs():
    with pytest.raises(ValidationError):
        RecommendationSearchRequest(
            user_id=1,
            current_latitude="37.405",
            current_longitude="126.721",
            destination_latitude="37.460",
            destination_longitude="126.450",
            remaining_range="45.0",
            actual_distance_km="40.0",
        )


def test_recommended_station_response_excludes_removed_nav_deeplink_field():
    payload = RecommendationDeliveryPayload(
        chrstn_mno="SCHEMA-REC-002",
        chrstn_nm="추천 충전소",
        road_nm_addr="인천광역시",
        oper_sttus_nm="운영 중",
        pressure_info="700bar 사용 가능",
        latitude=37.41,
        longitude=126.7,
        ntsl_pc=9500,
        distance_to_station=2.1,
        detour_distance=0.3,
        wait_vehicles=0,
        wait_time_minutes=0,
        facilities=["편의점"],
        is_reachable=True,
        final_score=98.1,
        recommendation_reason="가깝고 대기가 적습니다.",
    )
    response = RecommendedStationResponse(
        chrstn_mno="SCHEMA-REC-002",
        chrstn_nm="추천 충전소",
        road_nm_addr="인천광역시",
        ntsl_pc=9500,
        distance_to_station=2.1,
        distance_to_destination=20.0,
        detour_distance=0.3,
        wait_vehicles=0,
        wait_time_minutes=0,
        facilities=["편의점"],
        is_reachable=True,
        sub_scores=SubScores(price=90.0, waiting_time=100.0, distance=95.0, facilities=50.0),
        final_score=98.1,
        recommendation_reason="가깝고 대기가 적습니다.",
        delivery_payload=payload,
    )

    assert "hyundai_nav_deeplink" not in response.model_dump()
    assert response.delivery_payload.chrstn_mno == response.chrstn_mno


def test_user_create_validates_name_and_email_length():
    with pytest.raises(ValidationError):
        UserCreate(name="", email="empty-name@example.com")

    with pytest.raises(ValidationError):
        UserCreate(name="긴이름", email=f"{'a' * 256}@example.com")


def test_user_preference_update_defaults_all_weights():
    update = UserPreferenceUpdate()

    assert update.weight_price == Decimal("1.0")
    assert update.weight_waiting_time == Decimal("1.0")
    assert update.weight_distance == Decimal("1.0")
    assert update.weight_facilities == Decimal("1.0")
    assert update.safety_margin == Decimal("1.1")


def test_user_preference_learning_request_accepts_waiting_time_score_alias():
    request = UserPreferenceLearningRequest(
        chrstn_mno="SCHEMA-LEARN-001",
        price_score="40",
        waiting_time_score="90",
        distance_score="85",
        facilities_score="25",
    )

    assert request.waiting_score == Decimal("90")


def test_user_preference_learning_request_rejects_blank_station_id():
    with pytest.raises(ValidationError):
        UserPreferenceLearningRequest(chrstn_mno="")
