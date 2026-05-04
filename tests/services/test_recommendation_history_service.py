import pytest

from app.schemas.recommendation_history_schema import RecommendationHistoryCreate
from app.services.recommendation_history_service import RecommendationHistoryService
from tests.test_data_factory import seed_base_entities


@pytest.mark.asyncio
async def test_create_recommendation_history_success(db_session):
    base = await seed_base_entities(db_session)
    service = RecommendationHistoryService(db_session)

    row = await service.create_recommendation_history(
        RecommendationHistoryCreate(
            user_id=base["user"].user_id,
            vehicle_id=base["vehicle"].vehicle_id,
            hydrogen_station_id=base["station"].hydrogen_station_id,
            recommendation_score=90.0,
            recommendation_type="distance",
            selected=True,
        )
    )

    assert row.recommendation_id is not None
    assert row.selected is True
