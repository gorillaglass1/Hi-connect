import pytest

from app.schemas.hydrogen_station_schema import HydrogenStationCreate
from app.services.hydrogen_station_service import HydrogenStationService
from app.services.hydrogen_station_status_service import HydrogenStationStatusService


class FakeHyingClient:
    async def fetch_station_statuses(self, params=None):
        return [
            {
                "chrstn_mno": "ST-STATUS-001",
                "tt_pressr": 700,
                "wait_vhcle_alge": 2,
                "oper_sttus_cd": "OPEN",
                "oper_sttus_nm": "운영중",
            }
        ]


@pytest.mark.asyncio
async def test_sync_hydrogen_station_statuses_from_hying(db_session):
    await HydrogenStationService(db_session).create_hydrogen_station(
        HydrogenStationCreate(
            chrstn_mno="ST-STATUS-001",
            chrstn_nm="상태 테스트 충전소",
        )
    )
    service = HydrogenStationStatusService(db_session, hying_client=FakeHyingClient())

    result = await service.sync_from_hying()
    rows = await service.get_hydrogen_station_statuses(chrstn_mno="ST-STATUS-001")

    assert result == {"fetched": 1, "saved": 1, "skipped": 0}
    assert rows[0].oper_sttus_nm == "운영중"
