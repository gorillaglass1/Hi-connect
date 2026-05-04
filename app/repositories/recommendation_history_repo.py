from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recommendation_history import recommendation_history


async def create_recommendation_history(
    db: AsyncSession,
    user_id: int,
    vehicle_id: int,
    hydrogen_station_id: int,
    recommendation_score: float | None = None,
    recommendation_reason: str | None = None,
    user_latitude: float | None = None,
    user_longitude: float | None = None,
    vehicle_remaining_hydrogen: float | None = None,
    estimated_arrival_time: int | None = None,
    selected: bool = False,
    selected_at: datetime | None = None,
    recommendation_type: str | None = None,
):
    row = recommendation_history(
        user_id=user_id,
        vehicle_id=vehicle_id,
        hydrogen_station_id=hydrogen_station_id,
        recommendation_score=recommendation_score,
        recommendation_reason=recommendation_reason,
        user_latitude=user_latitude,
        user_longitude=user_longitude,
        vehicle_remaining_hydrogen=vehicle_remaining_hydrogen,
        estimated_arrival_time=estimated_arrival_time,
        selected=selected,
        selected_at=selected_at,
        recommendation_type=recommendation_type,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def get_recommendation_histories(
    db: AsyncSession,
    recommendation_id: int | None = None,
    user_id: int | None = None,
    vehicle_id: int | None = None,
    hydrogen_station_id: int | None = None,
    selected: bool | None = None,
    recommendation_type: str | None = None,
    limit: int = 100,
    offset: int = 0,
):
    query = select(recommendation_history)

    if recommendation_id is not None:
        query = query.where(
            recommendation_history.recommendation_id == recommendation_id
        )
    if user_id is not None:
        query = query.where(recommendation_history.user_id == user_id)
    if vehicle_id is not None:
        query = query.where(recommendation_history.vehicle_id == vehicle_id)
    if hydrogen_station_id is not None:
        query = query.where(
            recommendation_history.hydrogen_station_id == hydrogen_station_id
        )
    if selected is not None:
        query = query.where(recommendation_history.selected == selected)
    if recommendation_type is not None:
        query = query.where(
            recommendation_history.recommendation_type == recommendation_type
        )

    query = query.order_by(recommendation_history.recommendation_id.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()
