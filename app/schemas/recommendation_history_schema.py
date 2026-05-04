from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RecommendationHistoryCreate(BaseModel):
    user_id: int
    vehicle_id: int
    hydrogen_station_id: int
    recommendation_score: float | None = None
    recommendation_reason: str | None = None
    user_latitude: float | None = None
    user_longitude: float | None = None
    vehicle_remaining_hydrogen: float | None = None
    estimated_arrival_time: int | None = None
    selected: bool = False
    selected_at: datetime | None = None
    recommendation_type: str | None = None


class RecommendationHistoryResponse(RecommendationHistoryCreate):
    recommendation_id: int
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
