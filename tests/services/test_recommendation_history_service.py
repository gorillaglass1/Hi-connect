import pytest

from app.schemas.hydrogen_station_schema import HydrogenStationCreate
from app.schemas.recommendation_history_schema import (
    RecommendationHistoryCreate,
    RecommendationStationCreate,
)
from app.services.hydrogen_station_service import HydrogenStationService
from app.services.recommendation_history_service import RecommendationHistoryService


@pytest.mark.asyncio
async def test_create_recommendation_histories_returns_list(db_session):
    station_service = HydrogenStationService(db_session)
    await station_service.create_hydrogen_station(
        HydrogenStationCreate(
            chrstn_mno="REC-SVC-001",
            chrstn_nm="서비스 추천 충전소 1",
        )
    )
    await station_service.create_hydrogen_station(
        HydrogenStationCreate(
            chrstn_mno="REC-SVC-002",
            chrstn_nm="서비스 추천 충전소 2",
        )
    )

    rows = await RecommendationHistoryService(
        db_session
    ).create_recommendation_histories(
        RecommendationHistoryCreate(
            user_id=3,
            recommendations=[
                RecommendationStationCreate(
                    chrstn_mno="REC-SVC-001",
                    recommendation_score="95.00",
                ),
                RecommendationStationCreate(
                    chrstn_mno="REC-SVC-002",
                    recommendation_score="89.00",
                ),
            ],
        )
    )

    assert len(rows) == 2
    assert [row.chrstn_mno for row in rows] == ["REC-SVC-001", "REC-SVC-002"]
