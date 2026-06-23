from app.services.co2_service import (
    CO2_KG_PER_KM,
    TREE_ABSORB_KG_PER_YEAR,
    calculate_co2_saving,
)


def test_constants_match_spec():
    assert CO2_KG_PER_KM == 0.103
    assert TREE_ABSORB_KG_PER_YEAR == 6.6


def test_calculate_for_100km():
    saving = calculate_co2_saving(100)
    assert saving.saved_kg == 10.3
    assert saving.trees_equiv == round(10.3 / 6.6, 2)


def test_zero_distance():
    saving = calculate_co2_saving(0)
    assert saving.saved_kg == 0.0
    assert saving.trees_equiv == 0.0


def test_negative_distance_is_clamped():
    saving = calculate_co2_saving(-50)
    assert saving.saved_kg == 0.0
    assert saving.trees_equiv == 0.0
