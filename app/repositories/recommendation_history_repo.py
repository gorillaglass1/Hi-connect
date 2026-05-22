from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recommendation_history import RecommendationHistory
from app.schemas.recommendation_history_schema import RecommendationHistoryCreate


async def create_recommendation_histories(
    db: AsyncSession,
    payload: RecommendationHistoryCreate,
) -> list[RecommendationHistory]:
    rows = [
        RecommendationHistory(
            user_id=payload.user_id,
            vehicle_id=payload.vehicle_id,
            chrstn_mno=recommendation.chrstn_mno,
            recommendation_score=recommendation.recommendation_score,
            recommendation_reason=recommendation.recommendation_reason,
            user_latitude=payload.user_latitude,
            user_longitude=payload.user_longitude,
            vehicle_remaining_hydrogen=payload.vehicle_remaining_hydrogen,
            estimated_arrival_time=recommendation.estimated_arrival_time,
            selected=recommendation.selected,
            selected_at=recommendation.selected_at,
            recommendation_type=recommendation.recommendation_type,
        )
        for recommendation in payload.recommendations
    ]
    db.add_all(rows)
    await db.commit()

    for row in rows:
        await db.refresh(row)

    return rows


async def get_recommendation_histories(
    db: AsyncSession,
    recommendation_id: int | None = None,
    user_id: int | None = None,
    vehicle_id: int | None = None,
    chrstn_mno: str | None = None,
    selected: bool | None = None,
    recommendation_type: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[RecommendationHistory]:
    query = select(RecommendationHistory)

    if recommendation_id is not None:
        query = query.where(RecommendationHistory.recommendation_id == recommendation_id)
    if user_id is not None:
        query = query.where(RecommendationHistory.user_id == user_id)
    if vehicle_id is not None:
        query = query.where(RecommendationHistory.vehicle_id == vehicle_id)
    if chrstn_mno is not None:
        query = query.where(RecommendationHistory.chrstn_mno == chrstn_mno)
    if selected is not None:
        query = query.where(RecommendationHistory.selected == selected)
    if recommendation_type is not None:
        query = query.where(
            RecommendationHistory.recommendation_type == recommendation_type
        )

    query = (
        query.order_by(RecommendationHistory.recommendation_id.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(query)
    return list(result.scalars().all())
