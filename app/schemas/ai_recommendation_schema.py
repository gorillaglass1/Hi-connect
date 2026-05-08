import time
from datetime import datetime

from pydantic import BaseModel


class ai_recommendation_post(BaseModel):
    user_id: int
    vehicle_id: int
    location: dict[str, float] # {"latitude": 37.5665,"longitude": 126.978}
    navigation: navigation_data
    trigger: trigger
    preferences: hydrogen_preferences

class navigation_data(BaseModel):
    destination: dict[str, str] #  {"name": "부산역","latitude": 35.1151, "longitude": 129.0415}
    remaining_route_distance_km: float
    estimated_arrival_time: str
    estimated_remaining_range_at_arrival_km: float

class trigger(BaseModel):
    trigger_type: str
    reason: str
    range_threshold_km: float
    arrival_range_threshold_km: float
    fuel_threshold_percent: float

class hydrogen_preferences(BaseModel):
    preference_700bar: bool
    max_detour_km: float

class ai_recommendation_Response(BaseModel):
    recommendations: list[recommendation_station_Response]
    message: str
    created_at: datetime


class recommendation_station_Response(BaseModel):
    rank: int
    station_id: int
    name: str
    address: str
    latitude: float
    longitude: float
    selected_charger_id: int | None
    score: float
    reason: str
    highlight: str
    decision_factor: decision_factor_Response

class decision_factor_Response(BaseModel):
    reachable: bool
    estimated_arrival_range_km: float
    detour_distance_km: float
    estimated_wait_time_min: int
    price: float
    supports_700bar: bool | None
    station_status: str

