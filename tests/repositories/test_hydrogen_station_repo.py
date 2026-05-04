import pytest

from app.repositories.hydrogen_station_repo import get_hydrogen_stations
from tests.test_data_factory import seed_base_entities


@pytest.mark.asyncio
async def test_get_hydrogen_stations_filter_by_name(db_session):
    base = await seed_base_entities(db_session)
    rows = await get_hydrogen_stations(db_session, name=base["station"].name)
    assert len(rows) == 1
