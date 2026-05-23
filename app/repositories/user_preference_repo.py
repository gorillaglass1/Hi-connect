from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.user_preference import UserPreference
from app.schemas.user_preference_schemas import UserPreferenceUpdate


async def get_user_preferences(
    db: AsyncSession,
    user_id: int,
) -> UserPreference:
    # Check if preferences already exist
    stmt = select(UserPreference).where(UserPreference.user_id == user_id)
    result = await db.execute(stmt)
    pref = result.scalar_one_or_none()

    if pref is None:
        # Check if the user exists
        user_stmt = select(User).where(User.user_id == user_id)
        user_res = await db.execute(user_stmt)
        user = user_res.scalar_one_or_none()
        if user is None:
            # If user doesn't exist, create a dummy or raise error (we'll let service raise 404)
            return None

        # Lazy initialize default preferences
        pref = UserPreference(
            user_id=user_id,
            weight_price=1.0,
            weight_waiting_time=1.0,
            weight_distance=1.0,
            weight_facilities=1.0,
            safety_margin=1.1,
        )
        db.add(pref)
        await db.commit()
        await db.refresh(pref)

    return pref


async def update_user_preferences(
    db: AsyncSession,
    user_id: int,
    payload: UserPreferenceUpdate,
) -> UserPreference:
    pref = await get_user_preferences(db, user_id)
    if pref is None:
        return None

    pref.weight_price = payload.weight_price
    pref.weight_waiting_time = payload.weight_waiting_time
    pref.weight_distance = payload.weight_distance
    pref.weight_facilities = payload.weight_facilities
    pref.safety_margin = payload.safety_margin

    await db.commit()
    await db.refresh(pref)
    return pref


async def get_user(db: AsyncSession, user_id: int) -> User:
    stmt = select(User).where(User.user_id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user is not None:
        # Load preferences
        await get_user_preferences(db, user_id)
        # Refresh to load relationships
        await db.refresh(user)
    return user
