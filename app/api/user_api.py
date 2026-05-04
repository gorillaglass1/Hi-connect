from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.user_schema import UserCreate, UserResponse, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/user", tags=["user"])


@router.post("/signup", response_model=UserResponse, status_code=201)
async def signup_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    return await service.create_user(user)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, payload: UserUpdate, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    return await service.update_user(
        user_id=user_id,
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
    )
