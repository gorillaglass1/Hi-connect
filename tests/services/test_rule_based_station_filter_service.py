import pytest
from decimal import Decimal

from app.schemas.hydrogen_station_schema import HydrogenStationCreate
from app.schemas.hydrogen_station_status_schema import HydrogenStationStatusCreate
from app.schemas.hydrogen_station_facilities_schema import (
    HydrogenStationAdditionalInfoCreate,
)
from app.services.hydrogen_station_service import HydrogenStationService
from app.services.hydrogen_station_status_service import HydrogenStationStatusService
from app.services.hydrogen_station_facilities_service import (
    HydrogenStationFacilitiesService,
)
from app.services.rule_based_station_filter_service import (
    RuleBasedStationFilterService,
)


def test_parse_extracts_region_price_and_facility():
    service = RuleBasedStationFilterService(db=None)

    conditions = service.parse("인천에 있고 가격이 9,900원 이하인 세차장 있는 충전소")

    assert "인천" in conditions.regions
    assert conditions.max_price == 9900
    assert "세차" in conditions.facilities


def test_parse_extracts_no_wait_and_open_status():
    service = RuleBasedStationFilterService(db=None)

    conditions = service.parse("대기 차량이 없는 영업중인 충전소")

    assert conditions.require_no_wait is True
    assert conditions.require_open is True
    assert conditions.require_short_wait is False


def test_parse_extracts_short_wait_and_administrative_region():
    service = RuleBasedStationFilterService(db=None)

    conditions = service.parse("수원시 대기 적은 충전소")

    assert "수원시" in conditions.regions
    assert conditions.require_short_wait is True
    assert conditions.require_no_wait is False


def test_parse_returns_no_conditions_for_unrecognized_query():
    service = RuleBasedStationFilterService(db=None)

    conditions = service.parse("아무거나 추천해줘")

    assert conditions.has_any() is False


@pytest.mark.asyncio
async def test_execute_search_returns_none_when_no_conditions(db_session):
    service = RuleBasedStationFilterService(db_session)

    assert await service.execute_search("그냥 충전소 추천") is None


@pytest.mark.asyncio
async def test_execute_search_filters_by_region_price_and_facility(db_session):
    station_service = HydrogenStationService(db_session)
    status_service = HydrogenStationStatusService(db_session)
    facility_service = HydrogenStationFacilitiesService(db_session)

    # 매칭 대상: 인천, 9000원, 세차장 보유, 대기 0
    await station_service.create_hydrogen_station(
        HydrogenStationCreate(
            chrstn_mno="RULE-MATCH",
            chrstn_nm="규칙 매칭 충전소",
            road_nm_addr="인천광역시 남동구 1",
            ntsl_pc=9000,
            oper_yn="Y",
        )
    )
    await status_service.create_hydrogen_station_status(
        HydrogenStationStatusCreate(chrstn_mno="RULE-MATCH", wait_vhcle_alge=0)
    )
    await facility_service.create_hydrogen_station_facility(
        HydrogenStationAdditionalInfoCreate(
            chrstn_mno="RULE-MATCH", adi_info_se_nm="세차장"
        )
    )

    # 탈락: 서울 + 비쌈 + 세차장 없음
    await station_service.create_hydrogen_station(
        HydrogenStationCreate(
            chrstn_mno="RULE-MISS-REGION",
            chrstn_nm="서울 비싼 충전소",
            road_nm_addr="서울특별시 강남구 2",
            ntsl_pc=11000,
            oper_yn="Y",
        )
    )
    # 탈락: 인천이지만 세차장 없음
    await station_service.create_hydrogen_station(
        HydrogenStationCreate(
            chrstn_mno="RULE-MISS-FACILITY",
            chrstn_nm="인천 세차장 없는 충전소",
            road_nm_addr="인천광역시 중구 3",
            ntsl_pc=9000,
            oper_yn="Y",
        )
    )

    result = await RuleBasedStationFilterService(db_session).execute_search(
        "인천에 있고 9900원 이하인 세차장 있는 대기 없는 충전소"
    )

    assert result == ["RULE-MATCH"]


@pytest.mark.asyncio
async def test_execute_search_returns_empty_list_when_no_station_matches(db_session):
    await HydrogenStationService(db_session).create_hydrogen_station(
        HydrogenStationCreate(
            chrstn_mno="RULE-NO-MATCH",
            chrstn_nm="부산 충전소",
            road_nm_addr="부산광역시 해운대구",
            oper_yn="Y",
        )
    )

    result = await RuleBasedStationFilterService(db_session).execute_search(
        "제주 충전소만"
    )

    assert result == []
