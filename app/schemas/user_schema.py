from pydantic import BaseModel, ConfigDict, EmailStr


class UserCreate(BaseModel):
    name: str
    phone: str | None
    email: EmailStr | None


class UserUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    email: EmailStr | None = None


class UserResponse(UserCreate):
    user_id: int
    model_config = ConfigDict(from_attributes=True)
