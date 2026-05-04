from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def create_user(db: AsyncSession, name: str, email: str, phone: str):
    new_user = User(name=name, email=email, phone=phone)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def get_users(
    db: AsyncSession,
    user_id: int | None = None,
    email: str | None = None,
    name: str | None = None,
    phone: str | None = None,
    limit: int = 100,
    offset: int = 0,
):
    query = select(User)

    if user_id is not None:
        query = query.where(User.user_id == user_id)

    if email:
        query = query.where(User.email == email)

    if name:
        query = query.where(User.name == name)

    if phone:
        query = query.where(User.phone == phone)

    query = query.order_by(User.user_id.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()


async def update_user(
    db: AsyncSession,
    user_id: int,
    name: str | None = None,
    phone: str | None = None,
):
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        return None

    if name is not None:
        user.name = name
    if phone is not None:
        user.phone = phone

    await db.commit()
    await db.refresh(user)
    return user
