import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models.hydrogen_station import HydrogenStation
from app.services import dashboard_service as ds_module
from app.services.dashboard_llm_service import LlmInsight
from app.services.dashboard_service import DashboardService
from app.services.hydrogen_tip_service import get_tip_pool

# 서울시청 부근(사용자 위치)과 두 충전소.
USER_LAT, USER_LON = 37.5665, 126.9780
NEAR = dict(chrstn_mno="NEAR", chrstn_nm="가까운 충전소", lon=126.9785, let=37.5670, oper_yn="Y", del_at="0")
FAR = dict(chrstn_mno="FAR", chrstn_nm="먼 충전소", lon=127.0276, let=37.4979, oper_yn="Y", del_at="0")


@pytest_asyncio.fixture
async def db():
    """테스트별 격리된 인메모리 SQLite 세션."""
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


@pytest.fixture(autouse=True)
def clear_cache():
    ds_module._cache.clear()
    yield
    ds_module._cache.clear()


async def _seed(db, rows):
    db.add_all([HydrogenStation(**row) for row in rows])
    await db.commit()


def _fake_llm(service, insight):
    async def fake_generate(context, tip_catalog):
        return insight

    service.llm_service.generate = fake_generate


# --- 폴백: LLM 없음 -------------------------------------------------------
@pytest.mark.asyncio
async def test_fallback_without_llm_still_fills_co2_and_nearest(db):
    await _seed(db, [NEAR])
    service = DashboardService(db)
    _fake_llm(service, None)  # LLM 실패/미설정 시뮬레이션

    resp = await service.get_dashboard(USER_LAT, USER_LON, distance_km=100)

    assert resp.condition is None  # LLM 결과 없음 -> null
    assert resp.hydrogen_tip is not None and resp.hydrogen_tip.tip  # 기본 팁 채움
    assert resp.co2.saved_kg == 10.3  # 백엔드 계산은 항상
    assert resp.nearest_station is not None
    assert resp.nearest_station.chrstn_mno == "NEAR"


# --- LLM SQL 사용 ---------------------------------------------------------
@pytest.mark.asyncio
async def test_uses_llm_sql_result(db):
    await _seed(db, [NEAR, FAR])
    service = DashboardService(db)
    # LLM이 일부러 먼 충전소만 조회 -> 기본 조회였다면 NEAR가 나왔을 것.
    _fake_llm(
        service,
        LlmInsight(
            station_sql="SELECT chrstn_mno, chrstn_nm, lon, let FROM hydrogen_stations WHERE chrstn_mno='FAR'",
            condition={"score": 75, "grade": "주의", "briefing": "미세먼지 주의"},
            hydrogen_tip={"tip_id": "tip_cold_01", "context_label": "기온 -2°C 감지", "reason": "추천"},
        ),
    )

    resp = await service.get_dashboard(USER_LAT, USER_LON, distance_km=50)

    assert resp.nearest_station.chrstn_mno == "FAR"  # LLM SQL이 사용됨
    assert resp.condition.score == 75
    assert resp.condition.grade == "주의"
    pool = get_tip_pool()
    assert resp.hydrogen_tip.tip == pool.get("tip_cold_01").tip
    assert resp.hydrogen_tip.context_label == "기온 -2°C 감지"


# --- 안전하지 않은 SQL -> 기본 조회 폴백 ----------------------------------
@pytest.mark.asyncio
async def test_unsafe_llm_sql_falls_back_to_default_query(db):
    await _seed(db, [NEAR])
    service = DashboardService(db)
    _fake_llm(
        service,
        LlmInsight(
            station_sql="DROP TABLE hydrogen_stations",
            condition={},
            hydrogen_tip={},
        ),
    )

    resp = await service.get_dashboard(USER_LAT, USER_LON, distance_km=10)

    # 안전 검증 실패 -> 백엔드 기본 조회 -> 충전소 테이블 보존 및 nearest 계산.
    assert resp.nearest_station.chrstn_mno == "NEAR"


# --- 결과 없는 SQL -> 기본 조회 폴백 --------------------------------------
@pytest.mark.asyncio
async def test_empty_llm_sql_result_falls_back(db):
    await _seed(db, [NEAR])
    service = DashboardService(db)
    _fake_llm(
        service,
        LlmInsight(
            station_sql="SELECT chrstn_mno, chrstn_nm, lon, let FROM hydrogen_stations WHERE chrstn_mno='NONE'",
            condition={},
            hydrogen_tip={},
        ),
    )

    resp = await service.get_dashboard(USER_LAT, USER_LON, distance_km=10)
    assert resp.nearest_station.chrstn_mno == "NEAR"


# --- condition 검증 -------------------------------------------------------
@pytest.mark.asyncio
async def test_invalid_condition_grade_becomes_null(db):
    await _seed(db, [NEAR])
    service = DashboardService(db)
    _fake_llm(
        service,
        LlmInsight(
            station_sql="",
            condition={"score": 50, "grade": "최고", "briefing": "x"},  # 잘못된 grade
            hydrogen_tip={},
        ),
    )

    resp = await service.get_dashboard(USER_LAT, USER_LON, distance_km=10)
    assert resp.condition is None


@pytest.mark.asyncio
async def test_condition_score_is_clamped(db):
    await _seed(db, [NEAR])
    service = DashboardService(db)
    _fake_llm(
        service,
        LlmInsight(
            station_sql="",
            condition={"score": 250, "grade": "좋음", "briefing": "좋은 날입니다"},
            hydrogen_tip={},
        ),
    )

    resp = await service.get_dashboard(USER_LAT, USER_LON, distance_km=10)
    assert resp.condition.score == 100


# --- hydrogen_tip 안전 ----------------------------------------------------
@pytest.mark.asyncio
async def test_unknown_tip_id_falls_back_to_pool(db):
    await _seed(db, [NEAR])
    service = DashboardService(db)
    _fake_llm(
        service,
        LlmInsight(
            station_sql="",
            condition={},
            hydrogen_tip={"tip_id": "made-up-id", "context_label": "x", "reason": "y"},
        ),
    )

    resp = await service.get_dashboard(USER_LAT, USER_LON, distance_km=10)
    # 풀에 없는 ID -> 검수 풀의 본문으로 폴백(LLM 본문 생성 금지).
    pool = get_tip_pool()
    pool_bodies = {pool.get(item["tip_id"]).tip for item in pool.prompt_catalog()}
    assert resp.hydrogen_tip.tip in pool_bodies


@pytest.mark.asyncio
async def test_low_fuel_fallback_tip_uses_low_fuel_tag(db):
    await _seed(db, [NEAR])
    service = DashboardService(db)
    _fake_llm(service, None)  # LLM 없음 -> 컨텍스트 태그 기반 폴백 팁

    resp = await service.get_dashboard(USER_LAT, USER_LON, distance_km=10, fuel_percent=15)

    pool = get_tip_pool()
    low_fuel_bodies = {
        pool.get(item["tip_id"]).tip
        for item in pool.prompt_catalog()
        if "low_fuel" in item["tags"]
    }
    assert resp.hydrogen_tip.tip in low_fuel_bodies


# --- nearest 계산 ---------------------------------------------------------
@pytest.mark.asyncio
async def test_nearest_picks_closest_station(db):
    await _seed(db, [NEAR, FAR])
    service = DashboardService(db)
    _fake_llm(service, None)

    resp = await service.get_dashboard(USER_LAT, USER_LON, distance_km=10)

    assert resp.nearest_station.chrstn_mno == "NEAR"
    assert resp.nearest_station.distance_km < 1.0
    assert resp.nearest_station.status == "운영중"
    assert resp.nearest_station.congestion is None


@pytest.mark.asyncio
async def test_no_operating_station_nearest_is_none(db):
    await _seed(db, [dict(NEAR, oper_yn="N")])
    service = DashboardService(db)
    _fake_llm(service, None)

    resp = await service.get_dashboard(USER_LAT, USER_LON, distance_km=10)

    assert resp.nearest_station is None  # 운영 충전소 없음
    assert resp.co2.saved_kg == 1.03  # co2는 그래도 채워진다


# --- 캐싱 -----------------------------------------------------------------
@pytest.mark.asyncio
async def test_response_is_cached(db):
    await _seed(db, [NEAR])
    service = DashboardService(db)
    _fake_llm(service, None)

    first = await service.get_dashboard(USER_LAT, USER_LON, distance_km=10)

    # 캐시 히트면 LLM/생성 로직을 다시 타지 않아야 한다.
    async def fail_if_called(context, tip_catalog):
        raise AssertionError("캐시 히트 시 LLM을 다시 호출하면 안 된다")

    service.llm_service.generate = fail_if_called

    second = await service.get_dashboard(USER_LAT, USER_LON, distance_km=10)
    assert second is first
