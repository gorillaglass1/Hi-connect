from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.schemas.user_preference_schema import UserPreferenceLearningRequest
from app.services.user_preference_service import (
    DEFAULT_WEIGHT_TOTAL,
    _blend_weight,
    _current_weight_total,
    _history_to_score_values,
    _score_values_from_payload,
    _scores_to_observed_weights,
)


def test_current_weight_total_falls_back_when_all_weights_are_zero():
    assert _current_weight_total(
        {
            "weight_price": Decimal("0"),
            "weight_waiting_time": Decimal("0"),
            "weight_distance": Decimal("0"),
            "weight_facilities": Decimal("0"),
        }
    ) == DEFAULT_WEIGHT_TOTAL


def test_scores_to_observed_weights_normalizes_positive_scores_to_current_total():
    observed = _scores_to_observed_weights(
        {
            "weight_price": Decimal("40"),
            "weight_waiting_time": Decimal("30"),
            "weight_distance": Decimal("20"),
            "weight_facilities": Decimal("10"),
        },
        Decimal("4"),
    )

    assert observed == {
        "weight_price": Decimal("1.6"),
        "weight_waiting_time": Decimal("1.2"),
        "weight_distance": Decimal("0.8"),
        "weight_facilities": Decimal("0.4"),
    }


def test_scores_to_observed_weights_uses_equal_split_when_scores_are_not_positive():
    observed = _scores_to_observed_weights(
        {
            "weight_price": Decimal("0"),
            "weight_waiting_time": Decimal("-10"),
            "weight_distance": Decimal("0"),
            "weight_facilities": Decimal("-1"),
        },
        Decimal("4"),
    )

    assert set(observed.values()) == {Decimal("1")}


def test_blend_weight_rounds_and_clamps_to_supported_range():
    assert _blend_weight(Decimal("1.00"), Decimal("1.234")) == Decimal("1.02")
    assert _blend_weight(Decimal("3.00"), Decimal("20.00")) == Decimal("3.00")
    assert _blend_weight(Decimal("0.00"), Decimal("-20.00")) == Decimal("0.00")


def test_history_to_score_values_returns_none_for_missing_snapshot():
    history = SimpleNamespace(
        price_score=Decimal("10"),
        waiting_time_score=None,
        distance_score=Decimal("30"),
        facilities_score=Decimal("40"),
    )

    assert _history_to_score_values(history) is None


def test_history_to_score_values_maps_complete_snapshot_to_weight_keys():
    history = SimpleNamespace(
        price_score=Decimal("10"),
        waiting_time_score=Decimal("20"),
        distance_score=Decimal("30"),
        facilities_score=Decimal("40"),
    )

    assert _history_to_score_values(history) == {
        "weight_price": Decimal("10"),
        "weight_waiting_time": Decimal("20"),
        "weight_distance": Decimal("30"),
        "weight_facilities": Decimal("40"),
    }


def test_score_values_from_payload_returns_none_when_no_scores_are_supplied():
    payload = UserPreferenceLearningRequest(chrstn_mno="ST-001")

    assert _score_values_from_payload(payload) is None


def test_score_values_from_payload_requires_all_scores_for_client_fallback():
    payload = UserPreferenceLearningRequest(
        chrstn_mno="ST-001",
        price_score=Decimal("10"),
    )

    with pytest.raises(Exception) as exc_info:
        _score_values_from_payload(payload)

    assert getattr(exc_info.value, "status_code", None) == 422


def test_score_values_from_payload_accepts_waiting_time_score_alias():
    payload = UserPreferenceLearningRequest.model_validate(
        {
            "chrstn_mno": "ST-001",
            "price_score": "10",
            "waiting_time_score": "20",
            "distance_score": "30",
            "facilities_score": "40",
        }
    )

    assert _score_values_from_payload(payload) == {
        "weight_price": Decimal("10"),
        "weight_waiting_time": Decimal("20"),
        "weight_distance": Decimal("30"),
        "weight_facilities": Decimal("40"),
    }
