import pytest

from app.schemas.optimized_station_recommendation_schema import (
    OptimizedStationRecommendationRequest,
)
from app.services.optimized_station_recommendation_service import (
    OptimizedStationRecommendationService,
)


def optimized_payload():
    return {
        "user_id": 1,
        "vehicle": {
            "vehicle_id": 1,
            "model": "NEXO",
            "fuel_type": "hydrogen",
            "remaining_hydrogen_percent": 28,
            "remaining_range_km": 96,
            "tank_capacity_kg": 6.33,
            "avg_efficiency_km_per_kg": 96.0,
        },
        "location": {
            "latitude": 37.5665,
            "longitude": 126.978,
            "timestamp": "2026-05-08T10:30:00Z",
        },
        "navigation": {
            "destination": {
                "name": "부산역",
                "latitude": 35.1151,
                "longitude": 129.0415,
            },
            "remaining_route_distance_km": 390.5,
            "estimated_arrival_time": "2026-05-08T15:20:00Z",
            "estimated_remaining_range_at_arrival_km": 12,
            "route_polyline": "encoded_polyline_or_null",
        },
        "trigger": {
            "type": "LOW_RANGE",
            "reason": "주행가능거리가 임계값 이하입니다.",
            "range_threshold_km": 120,
            "arrival_range_threshold_km": 50,
            "fuel_threshold_percent": 30,
        },
        "preferences": {
            "prefer_700bar": True,
            "max_detour_km": 15,
            "prioritize": [
                "reachable",
                "wait_time",
                "price",
                "detour_distance",
                "charger_status",
            ],
        },
        "candidate_stations": [
            {
                "hydrogen_station_id": 101,
                "name": "양재 수소충전소",
                "address": "서울 서초구",
                "latitude": 37.4681,
                "longitude": 127.0387,
                "distance_from_current_km": 8.4,
                "detour_distance_km": 2.1,
                "is_on_route": True,
                "price_per_kg": 9900,
                "payment_supported": "card",
                "realtime": {
                    "available_chargers": 1,
                    "in_use_chargers": 1,
                    "queue_count": 2,
                    "avg_wait_time": 10,
                    "hydrogen_stock_kg": 120.5,
                    "station_status": "OPEN",
                    "updated_at": "2026-05-08T10:29:00Z",
                },
                "chargers": [
                    {
                        "hydrogen_charger_id": 1001,
                        "charger_status": "AVAILABLE",
                        "hydrogen_pressure_bar": 700,
                        "pressure_type": "700bar",
                    }
                ],
            },
            {
                "hydrogen_station_id": 102,
                "name": "원거리 수소스테이션",
                "address": "경기",
                "latitude": 37.1,
                "longitude": 127.2,
                "distance_from_current_km": 40,
                "detour_distance_km": 14,
                "is_on_route": False,
                "price_per_kg": 12000,
                "realtime": {
                    "available_chargers": 0,
                    "in_use_chargers": 2,
                    "queue_count": 4,
                    "avg_wait_time": 25,
                    "hydrogen_stock_kg": 5,
                    "station_status": "OPEN",
                },
                "chargers": [
                    {
                        "hydrogen_charger_id": 1002,
                        "charger_status": "IN_USE",
                        "hydrogen_pressure_bar": 700,
                        "pressure_type": "700bar",
                    }
                ],
            },
            {
                "hydrogen_station_id": 103,
                "name": "휴무 충전소",
                "address": "서울",
                "latitude": 37.5,
                "longitude": 127.0,
                "distance_from_current_km": 2,
                "detour_distance_km": 1,
                "realtime": {
                    "available_chargers": 2,
                    "in_use_chargers": 0,
                    "queue_count": 0,
                    "station_status": "CLOSED",
                },
                "chargers": [],
            },
        ],
    }


@pytest.mark.asyncio
async def test_recommend_selects_best_reachable_open_station():
    payload = OptimizedStationRecommendationRequest(**optimized_payload())

    response = await OptimizedStationRecommendationService().recommend(payload)

    assert response.recommended_station.hydrogen_station_id == 101
    assert response.recommended_station.selected_charger_id == 1001
    assert response.decision_factors.reachable is True
    assert response.decision_factors.supports_700bar is True
    assert response.alternatives[0].hydrogen_station_id == 102


@pytest.mark.asyncio
async def test_recommend_raises_when_no_candidate_available():
    data = optimized_payload()
    data["candidate_stations"] = [
        {
            **data["candidate_stations"][0],
            "distance_from_current_km": 200,
        }
    ]
    payload = OptimizedStationRecommendationRequest(**data)

    with pytest.raises(ValueError):
        await OptimizedStationRecommendationService().recommend(payload)
