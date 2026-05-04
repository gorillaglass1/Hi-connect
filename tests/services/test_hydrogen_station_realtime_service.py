import pytest

from app.schemas.hydrogen_station_realtime_schemas import HydrogenStationRealtimeCreate
from app.services.hydrogen_station_realtime_service import HydrogenStationRealtimeService
from tests.test_data_factory import seed_base_entities


@pytest.mark.asyncio
async def test_upsert_station_realtime_success(db_session):
    base = await seed_base_entities(db_session)
    service = HydrogenStationRealtimeService(db_session)

    row = await service.upsert_station_realtime(
        HydrogenStationRealtimeCreate(
            hydrogen_station_id=base["station"].hydrogen_station_id,
            available_chargers=1,
            in_use_chargers=2,
            queue_count=3,
            station_status="busy",
        )
    )

    assert row.hydrogen_station_id == base["station"].hydrogen_station_id
    assert row.queue_count == 3
