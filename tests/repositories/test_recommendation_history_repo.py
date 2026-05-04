import pytest

from app.repositories.recommendation_history_repo import get_recommendation_histories
from tests.test_data_factory import seed_all_entities


@pytest.mark.asyncio
async def test_get_recommendation_histories_filter_by_selected(db_session):
    await seed_all_entities(db_session)
    rows = await get_recommendation_histories(db_session, selected=True)
    assert len(rows) >= 1


@pytest.mark.asyncio
async def test_get_recommendation_histories_filter_by_type(db_session):
    await seed_all_entities(db_session)
    rows = await get_recommendation_histories(db_session, recommendation_type="distance")
    assert len(rows) >= 1
