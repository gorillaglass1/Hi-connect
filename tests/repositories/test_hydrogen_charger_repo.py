import pytest

from app.repositories.hydrogen_charger_repo import get_hydrogen_chargers
from tests.test_data_factory import seed_base_entities


@pytest.mark.asyncio
async def test_get_hydrogen_chargers_filter_by_station_id(db_session):
    base = await seed_base_entities(db_session)
    rows = await get_hydrogen_chargers(
        db_session,
        hydrogen_station_id=base["station"].hydrogen_station_id,
    )
    assert len(rows) >= 1
