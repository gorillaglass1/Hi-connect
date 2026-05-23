from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class UserPreferenceBase(BaseModel):
    weight_price: Decimal = Field(default=Decimal("1.0"), description="가격 가중치")
    weight_waiting_time: Decimal = Field(default=Decimal("1.0"), description="대기차량(시간) 가중치")
    weight_distance: Decimal = Field(default=Decimal("1.0"), description="우회거리 가중치")
    weight_facilities: Decimal = Field(default=Decimal("1.0"), description="편의시설 가중치")
    safety_margin: Decimal = Field(default=Decimal("1.1"), description="주행가능거리 최소 안전 계수")


class UserPreferenceUpdate(UserPreferenceBase):
    pass


class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="사용자 이름")
    phone: str | None = Field(default=None, max_length=20, description="사용자 전화번호")
    email: str | None = Field(default=None, max_length=255, description="사용자 이메일")


class UserPreferenceResponse(UserPreferenceBase):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    created_at: datetime
    updated_at: datetime


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    name: str
    phone: str | None = None
    email: str | None = None
    created_at: datetime
    preferences: UserPreferenceResponse | None = None
