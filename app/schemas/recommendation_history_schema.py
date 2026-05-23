from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class RecommendationStationCreate(BaseModel):
    chrstn_mno: str
    recommendation_score: Decimal | None = Field(default=None)
    recommendation_reason: str | None = Field(default=None)
    estimated_arrival_time: int | None = Field(default=None)
    selected: bool = Field(default=False)
    selected_at: datetime | None = Field(default=None)
    recommendation_type: str | None = Field(default=None)


class RecommendationHistoryCreate(BaseModel):
    user_id: int
    user_latitude: Decimal | None = Field(default=None)
    user_longitude: Decimal | None = Field(default=None)
    vehicle_remaining_hydrogen: Decimal | None = Field(default=None)
    recommendations: list[RecommendationStationCreate] = Field(min_length=1)


class RecommendationHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    recommendation_id: int
    user_id: int
    chrstn_mno: str
    recommendation_score: Decimal | None = Field(default=None)
    recommendation_reason: str | None = Field(default=None)
    user_latitude: Decimal | None = Field(default=None)
    user_longitude: Decimal | None = Field(default=None)
    vehicle_remaining_hydrogen: Decimal | None = Field(default=None)
    estimated_arrival_time: int | None = Field(default=None)
    selected: bool = Field(default=False)
    selected_at: datetime | None = Field(default=None)
    recommendation_type: str | None = Field(default=None)
    created_at: datetime | None = Field(default=None)
