from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


class VehicleContext(BaseModel):
    vehicle_id: int
    model: str
    fuel_type: str = "hydrogen"
    remaining_hydrogen_percent: int
    remaining_range_km: int
    tank_capacity_kg: float | None = None
    avg_efficiency_km_per_kg: float | None = None


class GeoPoint(BaseModel):
    latitude: float
    longitude: float


class CurrentLocation(GeoPoint):
    timestamp: str | None = None


class Destination(GeoPoint):
    name: str | None = None


class NavigationContext(BaseModel):
    destination: Destination | None = None
    remaining_route_distance_km: float | None = None
    estimated_arrival_time: str | None = None
    estimated_remaining_range_at_arrival_km: int | None = None
    route_polyline: str | None = None


class RecommendationTrigger(BaseModel):
    type: Literal["LOW_RANGE", "LOW_FUEL", "LOW_ARRIVAL_RANGE", "MANUAL"]
    reason: str
    range_threshold_km: int = 120
    arrival_range_threshold_km: int = 50
    fuel_threshold_percent: int = 30


class RecommendationPreferences(BaseModel):
    prefer_700bar: bool = True
    max_detour_km: float = 15
    prioritize: list[str] = Field(
        default_factory=lambda: [
            "reachable",
            "wait_time",
            "price",
            "detour_distance",
            "charger_status",
        ]
    )


class ChargerCandidate(BaseModel):
    hydrogen_charger_id: int
    charger_status: str
    hydrogen_pressure_bar: int | None = None
    pressure_type: str | None = None


class RealtimeStationStatus(BaseModel):
    available_chargers: int
    in_use_chargers: int
    queue_count: int
    avg_wait_time: int | None = None
    hydrogen_stock_kg: float | None = None
    station_status: str | None = None
    updated_at: str | None = None


class CandidateStation(BaseModel):
    hydrogen_station_id: int
    name: str
    address: str
    latitude: float
    longitude: float
    distance_from_current_km: float | None = None
    detour_distance_km: float | None = None
    is_on_route: bool = False
    price_per_kg: int | None = None
    payment_supported: str | None = None
    realtime: RealtimeStationStatus | None = None
    chargers: list[ChargerCandidate] = Field(default_factory=list)


class OptimizedStationRecommendationRequest(BaseModel):
    user_id: int
    vehicle: VehicleContext
    location: CurrentLocation
    navigation: NavigationContext | None = None
    trigger: RecommendationTrigger
    preferences: RecommendationPreferences = Field(default_factory=RecommendationPreferences)
    candidate_stations: list[CandidateStation]


class RecommendedStation(BaseModel):
    hydrogen_station_id: int
    name: str
    address: str
    latitude: float
    longitude: float
    selected_charger_id: int | None = None


class DecisionFactors(BaseModel):
    reachable: bool
    estimated_arrival_range_km: int
    detour_distance_km: float | None = None
    estimated_wait_time_min: int | None = None
    price_per_kg: int | None = None
    supports_700bar: bool
    station_status: str | None = None


class AlternativeStation(BaseModel):
    hydrogen_station_id: int
    name: str
    score: float
    reason: str


class RecommendedStationOption(BaseModel):
    rank: int
    hydrogen_station_id: int
    name: str
    address: str
    latitude: float
    longitude: float
    selected_charger_id: int | None = None
    score: float
    reason: str
    highlight: str
    decision_factors: DecisionFactors


class OptimizedStationRecommendationResponse(BaseModel):
    recommendation_id: int
    recommended_station: RecommendedStation
    score: float
    reason: str
    decision_factors: DecisionFactors
    recommendations: list[RecommendedStationOption]
    alternatives: list[AlternativeStation]
    message_for_driver: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GeminiRecommendationText(BaseModel):
    recommended_station_id: int | None = None
    reason: str | None = None
    message_for_driver: str | None = None
    raw: dict[str, Any] | None = None
