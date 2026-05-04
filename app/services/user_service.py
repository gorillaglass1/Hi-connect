from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import user_repo
from app.schemas.user_schema import UserCreate


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(self, user: UserCreate):
        existing_user = await user_repo.get_user_by_email(self.db, user.email)
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

    async def find_user_by_id(self, user_id: int):
        user = await user_repo.get_user_by_id(self.db, user_id)
        return {"user": user}
