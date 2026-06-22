import pytest

from app.services.recommendation_reason_service import (
    RecommendationReasonService,
    RecommendationWeights,
    StationReasonFacts,
)


def _facts(**overrides):
    base = dict(
        chrstn_nm="테스트 충전소",
        price_val=9000.0,
        min_price=9000.0,
        detour_distance=1.0,
        distance_to_station=5.0,
        service_available=True,
        wait_time_minutes=5,
        queue_reasons=[],
        facility_count=0,
        active_facilities=[],
        is_reachable=True,
    )
    base.update(overrides)
    return StationReasonFacts(**base)


def test_rule_based_reason_highlights_weighted_dimensions():
    service = RecommendationReasonService()
    weights = RecommendationWeights(price=2.0, wait=2.0, distance=2.0, facilities=2.0)

    reason = service.build_rule_based_reason(
        _facts(
            detour_distance=1.0,
            price_val=9000.0,
            min_price=9000.0,
            wait_time_minutes=5,
            facility_count=2,
            active_facilities=["편의점", "카페"],
        ),
        weights,
    )

    assert "우회 거리" in reason
    assert "저렴" in reason
    assert "대기시간" in reason
    assert "편의시설" in reason


def test_rule_based_reason_notes_unavailable_service():
    service = RecommendationReasonService()
    weights = RecommendationWeights(price=0.0, wait=2.0, distance=0.0, facilities=0.0)

    reason = service.build_rule_based_reason(
        _facts(service_available=False), weights
    )

    assert "운영/압력 상태" in reason


def test_rule_based_reason_notes_unreachable_station():
    service = RecommendationReasonService()
    weights = RecommendationWeights(price=0.0, wait=0.0, distance=0.0, facilities=0.0)

    reason = service.build_rule_based_reason(
        _facts(is_reachable=False), weights
    )

    assert "초과" in reason


@pytest.mark.asyncio
async def test_generate_reasons_falls_back_without_client():
    service = RecommendationReasonService()
    service.client = None  # No Gemini configured in test environment
    weights = RecommendationWeights(price=2.0, wait=0.0, distance=0.0, facilities=0.0)

    stations = [
        _facts(chrstn_nm="A", price_val=9000.0, min_price=9000.0),
        # 가격이 비싸 가격 사유가 트리거되지 않으므로 도달 불가 폴백 문구가 나온다.
        _facts(chrstn_nm="B", price_val=20000.0, min_price=9000.0, is_reachable=False),
    ]

    reasons = await service.generate_reasons(stations, weights)

    assert len(reasons) == 2
    assert "저렴" in reasons[0]
    assert "초과" in reasons[1]


@pytest.mark.asyncio
async def test_generate_reasons_uses_gemini_output_when_available(monkeypatch):
    service = RecommendationReasonService()
    weights = RecommendationWeights(price=2.0, wait=0.0, distance=0.0, facilities=0.0)
    stations = [_facts(chrstn_nm="A"), _facts(chrstn_nm="B")]

    # Simulate the switch turned on with a configured client and valid response.
    service.ai_enabled = True
    service.client = object()

    def fake_generate(stations_arg, weights_arg):
        return ["AI 추천 이유 A", "AI 추천 이유 B"]

    monkeypatch.setattr(service, "_generate_with_gemini", fake_generate)

    reasons = await service.generate_reasons(stations, weights)

    assert reasons == ["AI 추천 이유 A", "AI 추천 이유 B"]


@pytest.mark.asyncio
async def test_generate_reasons_skips_gemini_when_switch_disabled(monkeypatch):
    service = RecommendationReasonService()
    service.ai_enabled = False  # main config switch off (default)
    service.client = object()
    weights = RecommendationWeights(price=2.0, wait=0.0, distance=0.0, facilities=0.0)
    stations = [_facts(price_val=9000.0, min_price=9000.0)]

    def fail_if_called(stations_arg, weights_arg):
        raise AssertionError("Gemini must not be called when the switch is off")

    monkeypatch.setattr(service, "_generate_with_gemini", fail_if_called)

    reasons = await service.generate_reasons(stations, weights)

    assert len(reasons) == 1
    assert "저렴" in reasons[0]


@pytest.mark.asyncio
async def test_generate_reasons_falls_back_on_length_mismatch(monkeypatch):
    service = RecommendationReasonService()
    weights = RecommendationWeights(price=2.0, wait=0.0, distance=0.0, facilities=0.0)
    stations = [
        _facts(chrstn_nm="A", price_val=9000.0, min_price=9000.0),
        _facts(chrstn_nm="B", price_val=9000.0, min_price=9000.0),
    ]
    service.ai_enabled = True
    service.client = object()

    monkeypatch.setattr(
        service, "_generate_with_gemini", lambda s, w: ["only one"]
    )

    reasons = await service.generate_reasons(stations, weights)

    assert len(reasons) == 2
    assert all("저렴" in r for r in reasons)


def test_parse_reason_array_strips_markdown_fences():
    parsed = RecommendationReasonService._parse_reason_array(
        '```json\n["이유1", "이유2"]\n```'
    )
    assert parsed == ["이유1", "이유2"]


def test_parse_reason_array_returns_none_for_invalid_json():
    assert RecommendationReasonService._parse_reason_array("not json") is None
