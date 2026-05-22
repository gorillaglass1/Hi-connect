import pytest

from app.schemas.hydrogen_station_facilities import (
    HydrogenStationAdditionalInfoCreate,
)
from app.schemas.hydrogen_station_status_schemas import HydrogenStationStatusCreate
from app.schemas.hydrogen_stations_schemas import HydrogenStationCreate
from app.services.hydrogen_station_facilities_service import (
    HydrogenStationFacilitiesService,
)
from app.services.hydrogen_station_service import HydrogenStationService
from app.services.hydrogen_station_status_service import HydrogenStationStatusService


class FakeHyingClient:
    async def fetch_stations(self, params=None):
        return [
            {
                "chrstn_mno": "ST-001",
                "chrstn_nm": "테스트 수소충전소",
                "road_nm_addr": "서울시 중구",
            }
        ]


@pytest.mark.asyncio
async def test_sync_hydrogen_stations_from_hying(db_session):
    service = HydrogenStationService(db_session, hying_client=FakeHyingClient())

    result = await service.sync_from_hying({"pageNo": 1})
    rows = await service.get_hydrogen_stations(chrstn_mno="ST-001")

    assert result == {"fetched": 1, "saved": 1}
    assert rows[0].chrstn_nm == "테스트 수소충전소"


@pytest.mark.asyncio
async def test_get_hydrogen_station_detail(db_session):
    station_service = HydrogenStationService(db_session)
    await station_service.create_hydrogen_station(
        HydrogenStationCreate(
            chrstn_mno="ST-DETAIL-001",
            chrstn_nm="상세 테스트 충전소",
        )
    )
    await HydrogenStationStatusService(db_session).create_hydrogen_station_status(
        HydrogenStationStatusCreate(
            chrstn_mno="ST-DETAIL-001",
            oper_sttus_nm="운영중",
        )
    )
    await HydrogenStationFacilitiesService(db_session).create_hydrogen_station_facility(
        HydrogenStationAdditionalInfoCreate(
            chrstn_mno="ST-DETAIL-001",
            adi_info_se_nm="주차장",
        )
    )

    detail = await station_service.get_hydrogen_station_detail("ST-DETAIL-001")

    assert detail.chrstn_nm == "상세 테스트 충전소"
    assert detail.status.oper_sttus_nm == "운영중"
    assert detail.facilities[0].adi_info_se_nm == "주차장"


@pytest.mark.asyncio
async def test_get_hydrogen_station_details_by_conditions(db_session):
    station_service = HydrogenStationService(db_session)
    await station_service.create_hydrogen_station(
        HydrogenStationCreate(
            chrstn_mno="ST-SEARCH-001",
            chrstn_nm="서울 조건 검색 충전소",
            road_nm_addr="서울시 강남구 테헤란로",
            oper_yn="Y",
            rltm_info_yn="Y",
            rsvt_posbl_yn="N",
        )
    )
    await station_service.create_hydrogen_station(
        HydrogenStationCreate(
            chrstn_mno="ST-SEARCH-002",
            chrstn_nm="부산 조건 검색 충전소",
            road_nm_addr="부산시 해운대구",
            oper_yn="Y",
            rltm_info_yn="N",
            rsvt_posbl_yn="Y",
        )
    )
    await HydrogenStationStatusService(db_session).create_hydrogen_station_status(
        HydrogenStationStatusCreate(
            chrstn_mno="ST-SEARCH-001",
            oper_sttus_nm="운영중",
            pos_sttus_nm="영업중",
            cnf_sttus_nm="여유",
        )
    )
    await HydrogenStationStatusService(db_session).create_hydrogen_station_status(
        HydrogenStationStatusCreate(
            chrstn_mno="ST-SEARCH-002",
            oper_sttus_nm="운영중",
            pos_sttus_nm="영업마감",
            cnf_sttus_nm="혼잡",
        )
    )
    await HydrogenStationFacilitiesService(db_session).create_hydrogen_station_facility(
        HydrogenStationAdditionalInfoCreate(
            chrstn_mno="ST-SEARCH-001",
            adi_info_se_nm="화장실",
        )
    )

    rows = await station_service.get_hydrogen_station_details(
        address="서울",
        oper_yn="Y",
        rltm_info_yn="Y",
        pos_sttus_nm="영업중",
        facility_nm="화장실",
    )

    assert len(rows) == 1
    assert rows[0].chrstn_mno == "ST-SEARCH-001"
    assert rows[0].status.pos_sttus_nm == "영업중"
    assert rows[0].facilities[0].adi_info_se_nm == "화장실"


@pytest.mark.asyncio
async def test_get_hydrogen_station_details_filters_address_prefix_and_sorts_by_wait_queue(
    db_session,
):
    station_service = HydrogenStationService(db_session)
    for station in [
        HydrogenStationCreate(
            chrstn_mno="ST-INCHEON-001",
            chrstn_nm="인천 대기 많음",
            road_nm_addr="인천서비스광역시 남동구",
        ),
        HydrogenStationCreate(
            chrstn_mno="ST-INCHEON-002",
            chrstn_nm="인천 대기 적음",
            road_nm_addr="인천서비스광역시 연수구",
        ),
        HydrogenStationCreate(
            chrstn_mno="ST-NOT-INCHEON-001",
            chrstn_nm="주소 중간 인천",
            road_nm_addr="서울특별시 인천로",
        ),
    ]:
        await station_service.create_hydrogen_station(station)

    for status in [
        HydrogenStationStatusCreate(
            chrstn_mno="ST-INCHEON-001",
            pos_sttus_nm="영업중",
            wait_vhcle_alge=5,
        ),
        HydrogenStationStatusCreate(
            chrstn_mno="ST-INCHEON-002",
            pos_sttus_nm="영업중",
            wait_vhcle_alge=1,
        ),
        HydrogenStationStatusCreate(
            chrstn_mno="ST-NOT-INCHEON-001",
            pos_sttus_nm="영업중",
            wait_vhcle_alge=0,
        ),
    ]:
        await HydrogenStationStatusService(db_session).create_hydrogen_station_status(
            status
        )

    rows = await station_service.get_hydrogen_station_details(
        address="인천서비스",
        pos_sttus_nm="영업중",
        sort_by="wait_vhcle_alge",
        sort_order="asc",
    )

    assert [row.chrstn_mno for row in rows] == ["ST-INCHEON-002", "ST-INCHEON-001"]
    assert [row.status.wait_vhcle_alge for row in rows] == [1, 5]
