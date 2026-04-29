from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recommendation_history import RecommendationHistory


async def create_recommendation_history(
    db: AsyncSession,
    user_id: int,
    vehicle_id: int,
    hydrogen_station_id: int,
    recommendation_score: float,
    recommendation_reason: str | None,
    recommendation_type: str | None,
):
    row = RecommendationHistory(
        user_id=user_id,
        vehicle_id=vehicle_id,
        hydrogen_station_id=hydrogen_station_id,
        recommendation_score=recommendation_score,
        recommendation_reason=recommendation_reason,
        recommendation_type=recommendation_type,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def get_recommendations(
    db: AsyncSession,
    recommendation_id: int | None = None,
    user_id: int | None = None,
    vehicle_id: int | None = None,
    hydrogen_station_id: int | None = None,
    recommendation_type: str | None = None,
    selected: bool | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    limit: int = 100,
    offset: int = 0,
):
    query = select(RecommendationHistory)

    if recommendation_id is not None:
        query = query.where(RecommendationHistory.recommendation_id == recommendation_id)

    if user_id is not None:
        query = query.where(RecommendationHistory.user_id == user_id)

    if vehicle_id is not None:
        query = query.where(RecommendationHistory.vehicle_id == vehicle_id)

    if hydrogen_station_id is not None:
        query = query.where(RecommendationHistory.hydrogen_station_id == hydrogen_station_id)

    if recommendation_type:
        query = query.where(RecommendationHistory.recommendation_type == recommendation_type)

    if selected is not None:
        query = query.where(RecommendationHistory.selected == selected)

    if created_from:
        query = query.where(RecommendationHistory.created_at >= created_from)

    if created_to:
        query = query.where(RecommendationHistory.created_at <= created_to)

    query = query.order_by(RecommendationHistory.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()
