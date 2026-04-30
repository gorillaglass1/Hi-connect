from pydantic import BaseModel, ConfigDict, EmailStr


class UserCreate(BaseModel):
    name: str
    phone: str | None
    email: EmailStr | None


class UserResponse(UserCreate):
    user_id: int
    model_config = ConfigDict(from_attributes=True)
