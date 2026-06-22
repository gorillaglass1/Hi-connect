from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.user import User
from app.models.user_preference import UserPreference
from app.schemas.user_preference_schema import UserCreate, UserPreferenceUpdate


async def create_user(
    db: AsyncSession,
    payload: UserCreate,
) -> User:
    user = User(**payload.model_dump())
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def get_user_preferences(
    db: AsyncSession,
    user_id: int,
) -> UserPreference | None:
    stmt = select(UserPreference).where(UserPreference.user_id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_user_preferences(
    db: AsyncSession,
    user_id: int,
    payload: UserPreferenceUpdate,
) -> UserPreference:
    pref = UserPreference(user_id=user_id, **payload.model_dump())
    db.add(pref)
    await db.commit()
    await db.refresh(pref)
    return pref


async def update_user_preferences(
    db: AsyncSession,
    pref: UserPreference,
    payload: UserPreferenceUpdate,
) -> UserPreference:
    pref.weight_price = payload.weight_price
    pref.weight_waiting_time = payload.weight_waiting_time
    pref.weight_distance = payload.weight_distance
    pref.weight_facilities = payload.weight_facilities
    pref.safety_margin = payload.safety_margin

    await db.commit()
    await db.refresh(pref)
    return pref


async def get_user(db: AsyncSession, user_id: int) -> User:
    stmt = (
        select(User)
        .where(User.user_id == user_id)
        .options(selectinload(User.preferences))
        .execution_options(populate_existing=True)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
