from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RecommendationHistoryCreate(BaseModel):
    user_id: int
    vehicle_id: int
    hydrogen_station_id: int
    recommendation_score: float | None = Field(default=None)
    recommendation_reason: str | None = Field(default=None)
    user_latitude: float | None = Field(default=None)
    user_longitude: float | None = Field(default=None)
    vehicle_remaining_hydrogen: float | None = Field(default=None)
    estimated_arrival_time: int | None = Field(default=None)
    selected: bool = Field(default=False)
    selected_at: datetime | None = Field(default=None)
    recommendation_type: str | None = Field(default=None)


class RecommendationHistoryResponse(RecommendationHistoryCreate):
    recommendation_id: int
    created_at: datetime | None = Field(default=None)

    model_config = ConfigDict(from_attributes=True)
