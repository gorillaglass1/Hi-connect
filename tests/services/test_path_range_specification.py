import math

import pytest

from app.services import path_range_specification as path_range


def test_haversine_km_returns_zero_for_same_point():
    assert path_range.haversine_km(37.5, 127.0, 37.5, 127.0) == pytest.approx(0.0)


def test_haversine_km_is_symmetric():
    forward = path_range.haversine_km(37.5665, 126.9780, 35.1796, 129.0756)
    backward = path_range.haversine_km(35.1796, 129.0756, 37.5665, 126.9780)

    assert forward == pytest.approx(backward)
    assert forward > 300


def test_find_theta_binary_search_rejects_shorter_than_straight_route():
    with pytest.raises(ValueError, match="detour_ratio must be >= 1.0"):
        path_range.find_theta_binary_search(0.99)


def test_find_theta_binary_search_returns_zero_for_straight_route():
    assert path_range.find_theta_binary_search(1.0) == 0.0


def test_find_theta_binary_search_solves_expected_detour_ratio():
    theta = path_range.find_theta_binary_search(1.2)
    ratio = theta / (2 * math.sin(theta / 2))

    assert ratio == pytest.approx(1.2)


def test_clamp_inscribed_to_circumscribed_keeps_box_inside_outer_lng_range():
    inscribed = {
        "lat_min": 1,
        "lat_max": 2,
        "lng_min": -10,
        "lng_max": 10,
    }
    circumscribed = {
        "lat_min": 0,
        "lat_max": 3,
        "lng_min": -3,
        "lng_max": 4,
    }

    result = path_range.clamp_inscribed_to_circumscribed(
        inscribed,
        circumscribed,
    )

    assert result == {
        "lat_min": 1,
        "lat_max": 2,
        "lng_min": -3,
        "lng_max": 4,
    }


def test_apply_padding_expands_latitude_only():
    box = {
        "lat_min": 37.0,
        "lat_max": 38.0,
        "lng_min": 126.0,
        "lng_max": 127.0,
    }

    result = path_range.apply_padding(box, 5.0)

    assert result["lat_min"] < box["lat_min"]
    assert result["lat_max"] > box["lat_max"]
    assert result["lng_min"] == box["lng_min"]
    assert result["lng_max"] == box["lng_max"]


def test_split_ring_into_boxes_covers_expected_edges():
    inscribed = {
        "lat_min": 1,
        "lat_max": 3,
        "lng_min": 1,
        "lng_max": 3,
    }
    circumscribed = {
        "lat_min": 0,
        "lat_max": 4,
        "lng_min": 0,
        "lng_max": 4,
    }

    top, bottom, left, right = path_range.split_ring_into_boxes(
        inscribed,
        circumscribed,
    )

    assert top == {"lat_min": 0, "lat_max": 1, "lng_min": 1, "lng_max": 3}
    assert bottom == {"lat_min": 3, "lat_max": 4, "lng_min": 1, "lng_max": 3}
    assert left == {"lat_min": 0, "lat_max": 4, "lng_min": 0, "lng_max": 1}
    assert right == {"lat_min": 0, "lat_max": 4, "lng_min": 3, "lng_max": 4}


def test_is_in_box_includes_boundaries():
    box = {
        "lat_min": 37.0,
        "lat_max": 38.0,
        "lng_min": 126.0,
        "lng_max": 127.0,
    }

    assert path_range.is_in_box(37.0, 126.0, box) is True
    assert path_range.is_in_box(38.0, 127.0, box) is True
    assert path_range.is_in_box(38.1, 127.0, box) is False
