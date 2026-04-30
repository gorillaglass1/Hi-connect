from datetime import datetime
from pydantic import BaseModel
from sqlalchemy import Boolean, DateTime


class RecommendationHistoryCreate(BaseModel):
    recommendation_score : int
    recommendation_reason : str
    user_latitude : float
    user_longitude : float
    vehicle_remaining_hydrogen : float
    estimated_arrival_time : int
    selected : bool = False
    selected_at : datetime | None = None
    recommendation_type : str
class RecommendationHistoryUpdate(BaseModel):
    user_id : int
    vehicle_id : int
    hydrogen_station_id : int
    created_at : datetime