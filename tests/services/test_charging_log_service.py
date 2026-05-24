import pytest

from app.schemas.charging_log_schema import ChargingLogCreate, ChargingLogItemCreate
from app.schemas.hydrogen_station_schema import HydrogenStationCreate
from app.services.charging_log_service import ChargingLogService
from app.services.hydrogen_station_service import HydrogenStationService


@pytest.mark.asyncio
async def test_create_charging_logs_returns_list(db_session):
    station_service = HydrogenStationService(db_session)
    await station_service.create_hydrogen_station(
        HydrogenStationCreate(
            chrstn_mno="LOG-SVC-001",
            chrstn_nm="서비스 로그 충전소 1",
        )
    )
    await station_service.create_hydrogen_station(
        HydrogenStationCreate(
            chrstn_mno="LOG-SVC-002",
            chrstn_nm="서비스 로그 충전소 2",
        )
    )

    rows = await ChargingLogService(db_session).create_charging_logs(
        ChargingLogCreate(
            user_id=3,
            logs=[
                ChargingLogItemCreate(
                    chrstn_mno="LOG-SVC-001",
                    start_time="2026-05-22T08:00:00",
                    end_time="2026-05-22T08:10:00",
                ),
                ChargingLogItemCreate(
                    chrstn_mno="LOG-SVC-002",
                    start_time="2026-05-22T09:00:00",
                    end_time="2026-05-22T09:10:00",
                ),
            ],
        )
    )

    assert len(rows) == 2
    assert [row.chrstn_mno for row in rows] == ["LOG-SVC-001", "LOG-SVC-002"]
