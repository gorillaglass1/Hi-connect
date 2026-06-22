import pytest

from app.services.recommendation_candidate_filter_service import (
    RecommendationCandidateFilterService,
)


class FakeRuleBasedFilterService:
    def __init__(self, result):
        self.result = result
        self.received_query = None

    async def execute_search(self, natural_language_query: str):
        self.received_query = natural_language_query
        return self.result


@pytest.mark.asyncio
async def test_filter_by_natural_language_skips_blank_query():
    service = RecommendationCandidateFilterService(db=None)
    service.rule_based_filter_service = FakeRuleBasedFilterService(["ST-001"])

    assert await service.filter_by_natural_language(None) is None
    assert await service.filter_by_natural_language("   ") is None
    assert service.rule_based_filter_service.received_query is None


@pytest.mark.asyncio
async def test_filter_by_natural_language_returns_candidate_station_ids():
    service = RecommendationCandidateFilterService(db=None)
    service.rule_based_filter_service = FakeRuleBasedFilterService(["ST-001", "ST-002"])

    result = await service.filter_by_natural_language("인천 대기 적은 충전소")

    assert result == ["ST-001", "ST-002"]
    assert service.rule_based_filter_service.received_query == "인천 대기 적은 충전소"


@pytest.mark.asyncio
async def test_filter_by_natural_language_keeps_none_as_fallback_signal():
    service = RecommendationCandidateFilterService(db=None)
    service.rule_based_filter_service = FakeRuleBasedFilterService(None)

    assert await service.filter_by_natural_language("해석할 조건 없음") is None


@pytest.mark.asyncio
async def test_filter_by_natural_language_preserves_empty_list_as_no_match_signal():
    service = RecommendationCandidateFilterService(db=None)
    service.rule_based_filter_service = FakeRuleBasedFilterService([])

    assert await service.filter_by_natural_language("조건에 맞는 충전소 없음") == []
