from pydantic import BaseModel, ConfigDict, EmailStr


class UserCreate(BaseModel):
    name: str
    phone: str | None
    email: EmailStr | None


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = None
    phone: str | None = None


class UserResponse(UserCreate):
    user_id: int
    model_config = ConfigDict(from_attributes=True)
