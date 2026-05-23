from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.user_preference_schemas import (
    UserPreferenceUpdate,
    UserPreferenceResponse,
    UserResponse,
)
from app.services.user_preference_service import UserPreferenceService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await UserPreferenceService(db).get_user(user_id)


@router.get("/{user_id}/preferences", response_model=UserPreferenceResponse)
async def get_user_preferences(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    return await UserPreferenceService(db).get_user_preferences(user_id)


@router.put("/{user_id}/preferences", response_model=UserPreferenceResponse)
async def update_user_preferences(
    user_id: int,
    payload: UserPreferenceUpdate,
    db: AsyncSession = Depends(get_db),
):
    return await UserPreferenceService(db).update_user_preferences(user_id, payload)
