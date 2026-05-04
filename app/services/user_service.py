from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import user_repo
from app.schemas.user_schema import UserCreate


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(self, user: UserCreate):
        existing_users = await user_repo.get_users(self.db, email=user.email, limit=1)
        existing_user = existing_users[0] if existing_users else None
        if existing_user is not None:
            raise HTTPException(status_code=409, detail="Email already exists")

        try:
            return await user_repo.create_user(
                self.db,
                name=user.name,
                email=user.email,
                phone=user.phone,
            )
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(status_code=409, detail="Email already exists")

    async def get_user_by_id(self, user_id: int):
        users = await user_repo.get_users(self.db, user_id=user_id, limit=1)
        user = users[0] if users else None
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    async def get_users(
        self,
        user_id: int | None = None,
        email: str | None = None,
        name: str | None = None,
        phone: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ):
        return await user_repo.get_users(
            self.db,
            user_id=user_id,
            email=email,
            name=name,
            phone=phone,
            limit=limit,
            offset=offset,
        )

    async def update_user(
        self,
        user_id: int,
        name: str | None = None,
        email: str | None = None,
        phone: str | None = None,
    ):
        if email is not None:
            existing_users = await user_repo.get_users(self.db, email=email, limit=1)
            existing_user = existing_users[0] if existing_users else None
            if existing_user is not None and existing_user.user_id != user_id:
                raise HTTPException(status_code=409, detail="Email already exists")

        try:
            user = await user_repo.update_user(
                self.db,
                user_id=user_id,
                name=name,
                email=email,
                phone=phone,
            )
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(status_code=409, detail="Email already exists")

        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return user
