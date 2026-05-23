from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories import user_preference_repo
from app.schemas.user_preference_schemas import (
    UserCreate,
    UserPreferenceUpdate,
    UserPreferenceResponse,
    UserResponse,
)


class UserPreferenceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(self, payload: UserCreate) -> UserResponse:
        try:
            user = await user_preference_repo.create_user(self.db, payload)
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(
                status_code=409,
                detail="User email already exists",
            )

        await user_preference_repo.get_user_preferences(self.db, user.user_id)
        return await self.get_user(user.user_id)

    async def get_user_preferences(self, user_id: int) -> UserPreferenceResponse:
        pref = await user_preference_repo.get_user_preferences(self.db, user_id)
        if pref is None:
            raise HTTPException(
                status_code=404,
                detail=f"User with ID {user_id} not found",
            )
        return pref

    async def update_user_preferences(
        self,
        user_id: int,
        payload: UserPreferenceUpdate,
    ) -> UserPreferenceResponse:
        pref = await user_preference_repo.update_user_preferences(
            self.db,
            user_id,
            payload,
        )
        if pref is None:
            raise HTTPException(
                status_code=404,
                detail=f"User with ID {user_id} not found",
            )
        return pref

    async def get_user(self, user_id: int) -> UserResponse:
        user = await user_preference_repo.get_user(self.db, user_id)
        if user is None:
            raise HTTPException(
                status_code=404,
                detail=f"User with ID {user_id} not found",
            )
        return user
