import pytest

from app.repositories.hydrogen_station_realtime_repo import (
    get_station_realtime,
    upsert_station_realtime,
)
from tests.test_data_factory import seed_base_entities


@pytest.mark.asyncio
async def test_upsert_station_realtime_updates_existing_row(db_session):
    base = await seed_base_entities(db_session)

    first = await upsert_station_realtime(
        db_session,
        hydrogen_station_id=base["station"].hydrogen_station_id,
        queue_count=1,
    )
    second = await upsert_station_realtime(
        db_session,
        hydrogen_station_id=base["station"].hydrogen_station_id,
        queue_count=7,
    )

    assert first.realtime_id == second.realtime_id
    assert second.queue_count == 7


@pytest.mark.asyncio
async def test_get_station_realtime_filter_by_station_id(db_session):
    base = await seed_base_entities(db_session)
    await upsert_station_realtime(
        db_session,
        hydrogen_station_id=base["station"].hydrogen_station_id,
        station_status="open",
    )

    rows = await get_station_realtime(
        db_session,
        hydrogen_station_id=base["station"].hydrogen_station_id,
    )
    assert len(rows) == 1
