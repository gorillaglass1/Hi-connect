"""대시보드 통합 인사이트 오케스트레이션.

흐름: 컨텍스트 수집 → 단일 LLM 호출 → station_sql 검증/실행(폴백) →
정보 결합(condition/tip/co2/nearest_station) → 단일 응답.

단일 LLM 호출 파이프라인이므로 폴백이 가장 중요하다. LLM이 실패/타임아웃/
파싱 실패해도 co2 와 nearest_station 은 백엔드만으로 항상 채워 반환한다.
"""

import logging
import time

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hydrogen_station import HydrogenStation
from app.schemas.dashboard_schema import (
    Co2Insight,
    ConditionInsight,
    DashboardResponse,
    HydrogenTipInsight,
    NearestStationInsight,
)
from app.services.co2_service import calculate_co2_saving
from app.services.dashboard_llm_service import DashboardLlmService, LlmInsight
from app.services.geo_utils import haversine_km, location_grid_key
from app.services.hydrogen_tip_service import HydrogenTipPool, get_tip_pool
from app.services.sql_guard import UnsafeSqlError, validate_station_sql
from app.services.weather_context_service import WeatherContextService

logger = logging.getLogger("dashboard_service")

_VALID_GRADES = {"좋음", "주의", "나쁨"}
_BRIEFING_MAX_LEN = 40

# 통합 응답 캐시: [위치 그리드 + 10분 버킷 + 연료 구간] -> (만료시각, 응답)
_CACHE_TTL_SECONDS = 600
_TIME_BUCKET_SECONDS = 600
_cache: dict[str, tuple[float, DashboardResponse]] = {}


def _fuel_band(fuel_percent: float | None) -> str:
    if fuel_percent is None:
        return "na"
    return str(int(max(0.0, min(100.0, fuel_percent)) // 10) * 10)


def _cache_key(lat: float, lon: float, fuel_percent: float | None) -> str:
    bucket = int(time.time() // _TIME_BUCKET_SECONDS)
    return f"{location_grid_key(lat, lon)}|{bucket}|{_fuel_band(fuel_percent)}"


class DashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.weather_service = WeatherContextService()
        self.llm_service = DashboardLlmService()
        self.tip_pool: HydrogenTipPool = get_tip_pool()

    async def get_dashboard(
        self,
        lat: float,
        lon: float,
        distance_km: float,
        fuel_percent: float | None = None,
    ) -> DashboardResponse:
        cache_key = _cache_key(lat, lon, fuel_percent)
        cached = _cache.get(cache_key)
        if cached and cached[0] > time.time():
            return cached[1]

        # 1. 컨텍스트 수집 (LLM 호출 전, 백엔드가 직접)
        weather = await self.weather_service.collect(lat, lon)
        context = {
            "위치": {"lat": lat, "lon": lon},
            "주행거리_km": distance_km,
            "연료_퍼센트": fuel_percent,
            "날씨": weather.to_dict(),
        }

        # 2. 단일 LLM 호출
        insight = await self.llm_service.generate(
            context, self.tip_pool.prompt_catalog()
        )

        # 3. 충전소 조회 (LLM SQL 검증/실행, 실패 시 백엔드 기본 조회)
        stations = await self._fetch_stations(insight)

        # 4. 정보 결합
        response = DashboardResponse(
            condition=self._build_condition(insight),
            hydrogen_tip=self._build_tip(insight, weather, fuel_percent),
            co2=self._build_co2(distance_km),
            nearest_station=self._nearest_station(lat, lon, stations),
        )

        _cache[cache_key] = (time.time() + _CACHE_TTL_SECONDS, response)
        return response

    # --- 충전소 조회 ----------------------------------------------------
    async def _fetch_stations(self, insight: LlmInsight | None) -> list[dict]:
        """LLM의 station_sql 을 검증·실행한다. 실패하면 백엔드 기본 조회로 폴백."""
        if insight and insight.station_sql:
            try:
                safe_sql = validate_station_sql(insight.station_sql)
                result = await self.db.execute(text(safe_sql))
                rows = [dict(row) for row in result.mappings().all()]
                if rows:
                    return rows
                logger.info("LLM SQL 결과가 비어 기본 조회로 폴백합니다.")
            except UnsafeSqlError as exc:
                logger.warning("안전하지 않은 LLM SQL, 기본 조회로 폴백: %s", exc)
            except Exception as exc:  # pragma: no cover - 방어적
                await self.db.rollback()
                logger.error("LLM SQL 실행 실패, 기본 조회로 폴백: %s", exc)
        return await self._fetch_stations_default()

    async def _fetch_stations_default(self) -> list[dict]:
        """백엔드 기본 조회: 운영 중(oper_yn='Y', del_at='0') 충전소."""
        query = (
            select(
                HydrogenStation.chrstn_mno,
                HydrogenStation.chrstn_nm,
                HydrogenStation.lon,
                HydrogenStation.let,
                HydrogenStation.oper_yn,
            )
            .where(HydrogenStation.oper_yn == "Y")
            .where(HydrogenStation.del_at == "0")
        )
        try:
            result = await self.db.execute(query)
            return [dict(row) for row in result.mappings().all()]
        except Exception as exc:  # pragma: no cover - 방어적
            await self.db.rollback()
            logger.error("기본 충전소 조회 실패: %s", exc)
            return []

    # --- 최근접 충전소 (haversine, 백엔드 계산) -------------------------
    def _nearest_station(
        self, lat: float, lon: float, stations: list[dict]
    ) -> NearestStationInsight | None:
        nearest: NearestStationInsight | None = None
        best_distance = float("inf")
        for row in stations:
            s_lat = _to_float(_pick(row, ("let", "lat", "latitude")))
            s_lon = _to_float(_pick(row, ("lon", "lng", "longitude")))
            if s_lat is None or s_lon is None:
                continue
            distance = haversine_km(lat, lon, s_lat, s_lon)
            if distance < best_distance:
                best_distance = distance
                oper = _pick(row, ("oper_yn",))
                nearest = NearestStationInsight(
                    chrstn_mno=str(_pick(row, ("chrstn_mno",)) or ""),
                    name=str(_pick(row, ("chrstn_nm", "name")) or ""),
                    distance_km=round(distance, 2),
                    status="운영중" if oper in (None, "Y") else "운영중지",
                    congestion=None,
                )
        return nearest

    # --- condition ------------------------------------------------------
    def _build_condition(self, insight: LlmInsight | None) -> ConditionInsight | None:
        if not insight or not insight.condition:
            return None
        data = insight.condition
        try:
            score = int(data.get("score"))
            grade = data.get("grade")
            briefing = data.get("briefing")
            if grade not in _VALID_GRADES or not isinstance(briefing, str):
                return None
            score = max(0, min(100, score))
            return ConditionInsight(
                score=score,
                grade=grade,
                briefing=briefing.strip()[:_BRIEFING_MAX_LEN],
            )
        except (TypeError, ValueError):
            return None

    # --- hydrogen_tip ---------------------------------------------------
    def _build_tip(
        self, insight: LlmInsight | None, weather, fuel_percent: float | None
    ) -> HydrogenTipInsight:
        """tip_id 로 검수 풀에서 본문을 꺼내 결합. 본문은 LLM이 만들지 않는다."""
        if insight and insight.hydrogen_tip and self.tip_pool.has(
            insight.hydrogen_tip.get("tip_id")
        ):
            data = insight.hydrogen_tip
            tip = self.tip_pool.get(data.get("tip_id"))
            return HydrogenTipInsight(
                tip=tip.tip,
                context_label=str(data.get("context_label") or tip.title),
                reason=str(data.get("reason") or "오늘 상황에 맞춰 추천"),
            )

        # 폴백: 컨텍스트 태그 기반으로 검수 풀에서 결정적으로 선택.
        tip = self._fallback_tip(weather, fuel_percent)
        return HydrogenTipInsight(
            tip=tip.tip,
            context_label=tip.title,
            reason="오늘 상황에 맞춘 기본 추천",
        )

    def _fallback_tip(self, weather, fuel_percent: float | None):
        tag = "default"
        if fuel_percent is not None and fuel_percent <= 20:
            tag = "low_fuel"
        elif weather.temperature_c is not None and weather.temperature_c <= 0:
            tag = "cold"
        elif weather.air_grade in ("나쁨", "매우나쁨"):
            tag = "bad_air"
        for item in self.tip_pool.prompt_catalog():
            if tag in item["tags"]:
                return self.tip_pool.get(item["tip_id"])
        return self.tip_pool.default_tip

    # --- co2 ------------------------------------------------------------
    @staticmethod
    def _build_co2(distance_km: float) -> Co2Insight:
        saving = calculate_co2_saving(distance_km)
        return Co2Insight(saved_kg=saving.saved_kg, trees_equiv=saving.trees_equiv)


def _pick(row: dict, keys: tuple[str, ...]):
    for key in keys:
        if key in row and row[key] is not None:
            return row[key]
    return None


def _to_float(value) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
