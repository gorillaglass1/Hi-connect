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
    preference_700bar: bool = Field(default=True)
    max_detour_km: float = Field(..., ge=0)


class AiRecommendationRequest(BaseModel):
    user_id: int
    vehicle_id: int
    location: GeoPoint
    navigation: NavigationData
    trigger: RecommendationTrigger
    preferences: HydrogenPreferences


class AiDestinationPoint(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class AiNavigationData(BaseModel):
    destination: AiDestinationPoint
    remaining_route_distance_km: float = Field(..., ge=0)
    estimated_arrival_time: datetime
    estimated_remaining_range_at_arrival_km: float


class AiRecommendationTrigger(BaseModel):
    trigger_type: TriggerType
    range_threshold_km: float = Field(..., ge=0)
    arrival_range_threshold_km: float = Field(..., ge=0)
    fuel_threshold_percent: float = Field(..., ge=0, le=100)


class AiRecommendationGeminiRequest(BaseModel):
    location: GeoPoint
    navigation: AiNavigationData
    trigger: AiRecommendationTrigger
    preferences: HydrogenPreferences

    @classmethod
    def from_ai_recommendation_request(
        cls,
        request: AiRecommendationRequest,
    ) -> "AiRecommendationGeminiRequest":
        return cls(
            location=GeoPoint(
                latitude=round(request.location.latitude, 3),
                longitude=round(request.location.longitude, 3),
            ),
            navigation=AiNavigationData(
                destination=AiDestinationPoint(
                    latitude=round(request.navigation.destination.latitude, 3),
                    longitude=round(request.navigation.destination.longitude, 3),
                ),
                remaining_route_distance_km=request.navigation.remaining_route_distance_km,
                estimated_arrival_time=request.navigation.estimated_arrival_time,
                estimated_remaining_range_at_arrival_km=(
                    request.navigation.estimated_remaining_range_at_arrival_km
                ),
            ),
            trigger=AiRecommendationTrigger(
                trigger_type=request.trigger.trigger_type,
                range_threshold_km=request.trigger.range_threshold_km,
                arrival_range_threshold_km=request.trigger.arrival_range_threshold_km,
                fuel_threshold_percent=request.trigger.fuel_threshold_percent,
            ),
            preferences=request.preferences,
        )


AIRecommendationRequest = AiRecommendationRequest
GeminiAIRecommendationRequest = AiRecommendationGeminiRequest


class DecisionFactorResponse(BaseModel):
    reachable: bool
    estimated_arrival_range_km: float
    detour_distance_km: float
    estimated_wait_time_min: int = Field(..., ge=0)
    price: float = Field(..., ge=0)
    supports_700bar: bool | None = Field(default=None)
    station_status: StationStatus


class RecommendationStationResponse(BaseModel):
    rank: int = Field(..., ge=1)
    station_id: int
    name: str
    address: str
    latitude: float
    longitude: float
    selected_charger_id: int | None = Field(default=None)
    score: float = Field(..., ge=0, le=100)
    reason: str
    highlight: str
    decision_factor: DecisionFactorResponse


class AIRecommendationResponse(BaseModel):
    recommendations: list[RecommendationStationResponse]
    message: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
