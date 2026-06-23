from app.services.hydrogen_tip_service import get_tip_pool


def test_pool_loads_at_least_ten_tips():
    pool = get_tip_pool()
    assert len(pool.prompt_catalog()) >= 10


def test_get_known_tip_returns_body():
    pool = get_tip_pool()
    tip = pool.get("tip_cold_01")
    assert tip.tip_id == "tip_cold_01"
    assert tip.tip  # 본문이 비어 있지 않다.


def test_unknown_tip_id_falls_back_to_default():
    pool = get_tip_pool()
    fallback = pool.get("does-not-exist")
    assert fallback.tip_id == pool.default_tip.tip_id


def test_none_tip_id_falls_back_to_default():
    pool = get_tip_pool()
    assert pool.get(None).tip_id == pool.default_tip.tip_id


def test_has_checks_membership():
    pool = get_tip_pool()
    assert pool.has("tip_cold_01") is True
    assert pool.has("nope") is False
    assert pool.has(None) is False


def test_prompt_catalog_excludes_tip_body():
    # LLM에는 본문을 노출하지 않는다(선택용 메타데이터만).
    pool = get_tip_pool()
    for item in pool.prompt_catalog():
        assert set(item.keys()) == {"tip_id", "tags", "title"}


def test_catalog_covers_all_condition_tags():
    pool = get_tip_pool()
    all_tags = {tag for item in pool.prompt_catalog() for tag in item["tags"]}
    assert {"cold", "low_fuel", "bad_air", "default"} <= all_tags
