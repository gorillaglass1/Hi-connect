from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import recommendation_history_repo
from app.schemas.recommendation_history_schema import RecommendationHistoryCreate


class RecommendationHistoryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_recommendation_histories(
        self,
        payload: RecommendationHistoryCreate,
    ):
        try:
            return await recommendation_history_repo.create_recommendation_histories(
                self.db,
                payload,
            )
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(
                status_code=400,
                detail="One or more recommended hydrogen stations do not exist",
            )

    async def get_recommendation_histories(
        self,
        recommendation_id: int | None = None,
        user_id: int | None = None,
        vehicle_id: int | None = None,
        chrstn_mno: str | None = None,
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
            chrstn_mno=chrstn_mno,
            selected=selected,
            recommendation_type=recommendation_type,
            limit=limit,
            offset=offset,
        )
