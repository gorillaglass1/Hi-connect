from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, Field


class TriggerType(str, Enum):
    LOW_FUEL = "LOW_FUEL"
    ARRIVAL_RANGE_RISK = "ARRIVAL_RANGE_RISK"
    MANUAL = "MANUAL"


class StationStatus(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    MAINTENANCE = "MAINTENANCE"
    UNKNOWN = "UNKNOWN"


class GeoPoint(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class DestinationPoint(GeoPoint):
    name: str


class NavigationData(BaseModel):
    destination: DestinationPoint
    remaining_route_distance_km: float = Field(..., ge=0)
    estimated_arrival_time: datetime
    estimated_remaining_range_at_arrival_km: float


class RecommendationTrigger(BaseModel):
    trigger_type: TriggerType
    reason: str
    range_threshold_km: float = Field(..., ge=0)
    arrival_range_threshold_km: float = Field(..., ge=0)
    fuel_threshold_percent: float = Field(..., ge=0, le=100)


class HydrogenPreferences(BaseModel):
    preference_700bar: bool = True
    max_detour_km: float = Field(..., ge=0)


class AIRecommendationRequest(BaseModel):
    user_id: int
    vehicle_id: int
    location: GeoPoint
    navigation: NavigationData
    trigger: RecommendationTrigger
    preferences: HydrogenPreferences


class DecisionFactorResponse(BaseModel):
    reachable: bool
    estimated_arrival_range_km: float
    detour_distance_km: float
    estimated_wait_time_min: int = Field(..., ge=0)
    price: float = Field(..., ge=0)
    supports_700bar: bool | None
    station_status: StationStatus


class RecommendationStationResponse(BaseModel):
    rank: int = Field(..., ge=1)
    station_id: int
    name: str
    address: str
    latitude: float
    longitude: float
    selected_charger_id: int | None
    score: float = Field(..., ge=0, le=100)
    reason: str
    highlight: str
    decision_factor: DecisionFactorResponse


class AIRecommendationResponse(BaseModel):
    recommendations: list[RecommendationStationResponse]
    message: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))