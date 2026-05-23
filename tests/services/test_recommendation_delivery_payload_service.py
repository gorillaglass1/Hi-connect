from decimal import Decimal

from app.schemas.recommendation_request_schemas import (
    RecommendationSearchRequest,
    SubScores,
)
from app.services.recommendation_delivery_payload_service import (
    RecommendationDeliveryPayloadService,
)


def test_build_delivery_payload_contains_stable_external_contract():
    request = RecommendationSearchRequest(
        user_id=7,
        current_latitude=Decimal("37.405"),
        current_longitude=Decimal("126.721"),
        destination_latitude=Decimal("37.460"),
        destination_longitude=Decimal("126.450"),
        remaining_range=Decimal("45"),
        alpha=Decimal("15"),
        nl_query="인천에 있고 대기 차량이 적은 충전소",
    )
    scores = SubScores(price=90.0, waiting_time=100.0, distance=82.5, facilities=50.0)

    payload = RecommendationDeliveryPayloadService.build(
        request=request,
        recommendation_type="SEMANTIC_AI",
        chrstn_mno="REC-ST-001",
        chrstn_nm="인천공항 수소충전소",
        station_latitude=37.46,
        station_longitude=126.45,
        station_address="인천광역시 중구",
        distance_to_station=12.34,
        distance_to_destination=0.25,
        detour_distance=1.5,
        is_reachable=True,
        scores=scores,
        final_score=94.2,
        recommendation_reason="사용자 가중치 분석 결과 전반적 매칭도가 매우 높습니다.",
    )

    assert payload.schema_version == "1.0"
    assert payload.source == "HY_CONNECT"
    assert payload.user_id == 7
    assert payload.recommendation_type == "SEMANTIC_AI"
    assert payload.station.chrstn_mno == "REC-ST-001"
    assert payload.station.name == "인천공항 수소충전소"
    assert payload.station.location.latitude == 37.46
    assert payload.route_context.current_location.longitude == 126.721
    assert payload.route_context.remaining_range_km == 45.0
    assert payload.route_context.is_reachable is True
    assert payload.scores == scores
    assert payload.final_score == 94.2
