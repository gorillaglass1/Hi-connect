import pytest

from app.schemas.hydrogen_stations_schemas import HydrogenStationCreate
from app.services.hydrogen_station_facilities_service import (
    HydrogenStationFacilitiesService,
)
from app.services.hydrogen_station_service import HydrogenStationService


class FakeHyingClient:
    def __init__(self):
        self.params = "not-called"

    async def fetch_station_facilities(self, params=None):
        self.params = params
        return [
            {
                "chrstn_mno": "ST-FAC-001",
                "adi_info_se_cd": "PARK",
                "adi_info_se_nm": "주차장",
            }
        ]


@pytest.mark.asyncio
async def test_sync_hydrogen_station_facilities_from_hying(db_session):
    await HydrogenStationService(db_session).create_hydrogen_station(
        HydrogenStationCreate(
            chrstn_mno="ST-FAC-001",
            chrstn_nm="부대시설 테스트 충전소",
        )
    )
    hying_client = FakeHyingClient()
    service = HydrogenStationFacilitiesService(db_session, hying_client=hying_client)

    result = await service.sync_from_hying()
    rows = await service.get_hydrogen_station_facilities(chrstn_mno="ST-FAC-001")

    assert result == {"fetched": 1, "saved": 1, "skipped": 0}
    assert hying_client.params is None
    assert rows[0].adi_info_se_nm == "주차장"
