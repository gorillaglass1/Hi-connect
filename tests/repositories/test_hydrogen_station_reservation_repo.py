from datetime import datetime, timedelta

import pytest

from app.repositories.hydrogen_station_reservation_repo import get_reservations
from tests.test_data_factory import seed_all_entities


@pytest.mark.asyncio
async def test_get_reservations_filter_by_user_id(db_session):
    seeded = await seed_all_entities(db_session)
    rows = await get_reservations(db_session, user_id=seeded["user"].user_id)
    assert len(rows) >= 1


@pytest.mark.asyncio
async def test_get_reservations_filter_by_reservation_time(db_session):
    seeded = await seed_all_entities(db_session)
    rows = await get_reservations(
        db_session,
        reservation_time=seeded["reservation"].reservation_time,
    )
    assert len(rows) == 1
