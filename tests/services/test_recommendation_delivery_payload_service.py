from app.services.recommendation_delivery_payload_service import (
    RecommendationDeliveryPayloadService,
)


def test_build_delivery_payload_contains_stable_external_contract():
    payload = RecommendationDeliveryPayloadService.build(
        chrstn_mno="REC-ST-001",
        chrstn_nm="인천공항 수소충전소",
        station_latitude=37.46,
        station_longitude=126.45,
        station_address="인천광역시 중구",
        ntsl_pc=9900,
        distance_to_station=12.34,
        detour_distance=1.5,
        wait_vehicles=0,
        wait_time_minutes=0,
        facilities=["편의점"],
        is_reachable=True,
        final_score=94.2,
        recommendation_reason="사용자 가중치 분석 결과 전반적 매칭도가 매우 높습니다.",
    )

    assert payload.chrstn_mno == "REC-ST-001"
    assert payload.chrstn_nm == "인천공항 수소충전소"
    assert payload.latitude == 37.46
    assert payload.longitude == 126.45
    assert payload.ntsl_pc == 9900
    assert payload.distance_to_station == 12.34
    assert payload.detour_distance == 1.5
    assert payload.wait_vehicles == 0
    assert payload.wait_time_minutes == 0
    assert payload.facilities == ["편의점"]
    assert payload.is_reachable is True
    assert payload.final_score == 94.2
    assert not hasattr(payload, "hyundai_nav_deeplink")
