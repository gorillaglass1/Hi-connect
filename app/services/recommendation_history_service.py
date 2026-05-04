from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import recommendation_history_repo
from app.schemas.recommendation_history_schema import RecommendationHistoryCreate


class RecommendationHistoryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_recommendation_history(self, payload: RecommendationHistoryCreate):
        return await recommendation_history_repo.create_recommendation_history(
            self.db,
            user_id=payload.user_id,
            vehicle_id=payload.vehicle_id,
            hydrogen_station_id=payload.hydrogen_station_id,
            recommendation_score=payload.recommendation_score,
            recommendation_reason=payload.recommendation_reason,
            user_latitude=payload.user_latitude,
            user_longitude=payload.user_longitude,
            vehicle_remaining_hydrogen=payload.vehicle_remaining_hydrogen,
            estimated_arrival_time=payload.estimated_arrival_time,
            selected=payload.selected,
            selected_at=payload.selected_at,
            recommendation_type=payload.recommendation_type,
        )

    async def get_recommendation_histories(
        self,
        recommendation_id: int | None = None,
        user_id: int | None = None,
        vehicle_id: int | None = None,
        hydrogen_station_id: int | None = None,
        selected: bool | None = None,
        recommendation_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ):
        return await recommendation_history_repo.get_recommendation_histories(
            self.db,
            recommendation_id=recommendation_id,
            user_id=user_id,
            vehicle_id=vehicle_id,
            hydrogen_station_id=hydrogen_station_id,
            selected=selected,
            recommendation_type=recommendation_type,
            limit=limit,
            offset=offset,
        )
