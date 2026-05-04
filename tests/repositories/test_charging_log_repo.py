import pytest

from app.repositories.charging_log_repo import get_charging_log_by_id, get_charging_logs
from tests.test_data_factory import seed_all_entities


@pytest.mark.asyncio
async def test_get_charging_log_by_id_success(db_session):
    seeded = await seed_all_entities(db_session)
    row = await get_charging_log_by_id(db_session, seeded["charging_log"].charging_log_id)
    assert row is not None


@pytest.mark.asyncio
async def test_get_charging_logs_filter_by_user_id(db_session):
    seeded = await seed_all_entities(db_session)
    rows = await get_charging_logs(db_session, user_id=seeded["user"].user_id)
    assert len(rows) >= 1
