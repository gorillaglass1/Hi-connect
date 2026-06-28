import asyncio
import json
import logging
import os
import re

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import is_dashboard_ai_enabled
from app.models.hydrogen_station_status import HydrogenStationStatus
from app.repositories import hydrogen_station_repo
from app.schemas.nearest_recommendation_schema import (
    DrivingHabit,
    NearestRecommendationInsight,
    NearestRecommendationMetric,
    NearestRecommendationRequest,
    NearestRecommendationResponse,
    NearestRecommendationStation,
    NearestRecommendationVehicleResponse,
)
from app.services import nearest_recommendation_prompt as prompt_manager
from app.services.recommendation_service import haversine_distance
from app.services.sql_guard import UnsafeSqlError, validate_station_sql

logger = logging.getLogger("nearest_recommendation_service")

try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_TIMEOUT_SECONDS = 60.0
TANK_CAPACITY_KG = 6.33
FUEL_SUFFICIENT_THRESHOLD = 50
FUEL_RECOMMEND_THRESHOLD = 25
HIGH_EVENTS_PER_HOUR = 2.0  # 이상이면 소모율 "다소 높음" 판정
AVG_CITY_SPEED_KMH = 25.0   # eta_minutes 근사용 도심 평균 속도
AVAILABLE_WAIT_LIMIT = 5    # 대기 차량 이 값 미만이면 available=True

# status -> (라벨, 부제목, 폴백 충전 시점)
_FALLBACK_LABELS = {
    "sufficient": ("충분", "잔량 충분", "여유 있음"),
    "recommend": ("충전 권장", "충전 권장 구간", "곧 충전 권장"),
    "urgent": ("긴급", "긴급 충전 필요", "즉시 충전"),
}
NO_STATION_MESSAGE = "근처에 충전소 정보가 없어요. 잠시 후 다시 시도해 주세요."


def determine_status(fuel_percent: int) -> str:
    if fuel_percent >= FUEL_SUFFICIENT_THRESHOLD:
        return "sufficient"
    if fuel_percent >= FUEL_RECOMMEND_THRESHOLD:
        return "recommend"
    return "urgent"


def _estimated_cost(fuel_percent: int, price: int | None) -> int:
    if not price:
        return 0
    return round(TANK_CAPACITY_KG * (1 - fuel_percent / 100) * price)


def _consumption_from_habit(habit: DrivingHabit | None) -> tuple[str, str]:
    """운전습관 기반 (소모율 표시값, tone)."""
    if habit is None or habit.style == "unknown":
        return "정상", "neutral"
    if habit.style == "aggressive" or habit.events_per_hour >= HIGH_EVENTS_PER_HOUR:
        return "다소 높음", "warning"
    if habit.style == "calm":
        return "낮음", "positive"
    return "정상", "neutral"


def _fallback_message(status: str, remaining_range: float) -> str:
    return {
        "sufficient": f"잔량이 넉넉해요. 약 {remaining_range}km 더 주행할 수 있어요.",
        "recommend": f"슬슬 충전을 준비하세요. 약 {remaining_range}km 주행 가능해요.",
        "urgent": f"지금 충전이 필요해요. 남은 주행가능거리는 약 {remaining_range}km예요.",
    }[status]


def _eta_minutes(distance_km: float) -> int:
    """경로 API 미연동 시 거리 기반 근사 (도심 평균 속도 가정)."""
    if not distance_km:
        return 0
    return round(distance_km / AVG_CITY_SPEED_KMH * 60)


def _station_badge(ntsl_pc: int | None, min_price: float | None, wait: int | None) -> str | None:
    """근거가 있을 때만 강조 칩을 부여한다."""
    if ntsl_pc is not None and min_price is not None and ntsl_pc <= min_price:
        return "근처 최저가"
    if wait == 0:
        return "대기 없음"
    return None


def _metrics(
    remaining_range: float, timing: str, consumption: str, tone: str
) -> list[NearestRecommendationMetric]:
    return [
        NearestRecommendationMetric(label="주행가능거리", value=str(remaining_range), unit="km"),
        NearestRecommendationMetric(label="권장 충전 시점", value=timing),
        NearestRecommendationMetric(label="예상 소모율", value=consumption, tone=tone),
    ]


class NearestRecommendationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_enabled = is_dashboard_ai_enabled()
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.client = None
        if self.ai_enabled and HAS_GENAI and self.api_key:
            try:
                self.client = genai.Client(
                    api_key=self.api_key,
                    http_options=types.HttpOptions(
                        timeout=int(GEMINI_TIMEOUT_SECONDS * 1000)
                    ),
                )
            except Exception as e:
                logger.error(f"Gemini 클라이언트 초기화 실패: {e}")

    # ===== Gemini 단일 호출 (SQL + insight) =====

    async def _call_gemini_combined(
        self,
        status: str,
        fuel_percent: int,
        remaining_range: float,
        lat: float,
        lon: float,
        radius_km: float,
        driving_habit: DrivingHabit | None,
    ) -> dict | None:
        """SQL + insight를 단일 Gemini 호출로 생성한다. 실패 시 None."""
        if not self.client:
            return None

        user_prompt = prompt_manager.build_prompt(
            status=status,
            fuel_percent=fuel_percent,
            remaining_range=remaining_range,
            lat=lat,
            lon=lon,
            radius_km=radius_km,
            driving_habit=driving_habit,
        )
        try:
            raw_text = await asyncio.wait_for(
                asyncio.to_thread(self._gemini_generate, user_prompt),
                timeout=GEMINI_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            logger.warning(f"Gemini 타임아웃 ({GEMINI_TIMEOUT_SECONDS}s)")
            return None
        except Exception as e:
            logger.error(f"Gemini 호출 실패: {e}")
            return None
        return self._parse_combined(raw_text)

    def _gemini_generate(self, user_prompt: str) -> str | None:
        response = self.client.models.generate_content(
            model=GEMINI_MODEL,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=prompt_manager.SYSTEM_INSTRUCTION,
                temperature=prompt_manager.GENERATION_TEMPERATURE,
                response_mime_type="application/json",
            ),
        )
        return response.text

    @staticmethod
    def _parse_combined(raw_text: str | None) -> dict | None:
        """Gemini 응답 JSON을 파싱한다. 실패 시 None."""
        if not raw_text:
            return None
        cleaned = re.sub(r"```(?:json)?\s*", "", raw_text, flags=re.IGNORECASE)
        cleaned = cleaned.replace("```", "").strip()
        try:
            parsed = json.loads(cleaned)
        except (json.JSONDecodeError, ValueError):
            return None
        return parsed if isinstance(parsed, dict) else None

    # ===== 충전소 조회 =====

    async def _load_priced_candidates(
        self, lat: float, lon: float, radius_km: float
    ) -> tuple[list[tuple[float, object]], float | None, float | None]:
        """반경 내 가격 있는 후보 목록과 (평균가, 최저가)를 한 번의 조회로 반환한다."""
        stations = await hydrogen_station_repo.get_active_hydrogen_stations_for_recommendation(
            self.db
        )
        candidates = []
        for st in stations:
            if st.let is None or st.lon is None or st.ntsl_pc is None:
                continue
            dist = haversine_distance(lat, lon, float(st.let), float(st.lon))
            if dist <= radius_km:
                candidates.append((dist, st))
        prices = [c[1].ntsl_pc for c in candidates]
        avg_price = sum(prices) / len(prices) if prices else None
        min_price = min(prices) if prices else None
        return candidates, avg_price, min_price

    def _make_station(
        self,
        *,
        chrstn_mno: str,
        name: str,
        road: str | None,
        dist: float,
        ntsl_pc: int | None,
        is_open: bool,
        wait: int | None,
        lat_: float,
        lon_: float,
        avg_price: float | None,
        min_price: float | None,
        realtime: bool,
        fuel_percent: int,
    ) -> NearestRecommendationStation:
        price_diff = (
            round(ntsl_pc - avg_price, 1) if avg_price is not None and ntsl_pc else 0.0
        )
        return NearestRecommendationStation(
            chrstn_mno=chrstn_mno,
            name=name,
            road_nm_addr=road,
            distance_km=round(dist, 2),
            ntsl_pc=ntsl_pc,
            price_diff_from_avg=price_diff,
            estimated_cost=_estimated_cost(fuel_percent, ntsl_pc),
            wait_vhcle_alge=wait,
            is_open=is_open,
            let=float(lat_),
            lon=float(lon_),
            badge=_station_badge(ntsl_pc, min_price, wait),
            realtime_price=realtime,
            eta_minutes=_eta_minutes(dist),
            available=is_open and (wait or 0) < AVAILABLE_WAIT_LIMIT,
        )

    async def _fetch_station_by_sql(
        self,
        raw_sql: str,
        lat: float,
        lon: float,
        radius_km: float,
        fuel_percent: int,
        avg_price: float | None,
        min_price: float | None,
    ) -> NearestRecommendationStation | None:
        """Gemini가 생성한 SQL로 최적(최저가) 충전소 1곳을 찾는다. 실패 시 None."""
        try:
            safe_sql = validate_station_sql(raw_sql)
            rows = (await self.db.execute(text(safe_sql))).mappings().all()
        except UnsafeSqlError as e:
            logger.warning(f"SQL 검증 실패 (Python 폴백): {e}")
            return None
        except Exception as e:
            logger.warning(f"SQL 실행 실패 (Python 폴백): {e}")
            return None

        candidates = []
        for row in rows:
            if row.get("let") is None or row.get("lon") is None:
                continue
            dist = haversine_distance(lat, lon, float(row["let"]), float(row["lon"]))
            if dist <= radius_km:
                candidates.append((dist, row))
        if not candidates:
            return None

        dist, row = min(candidates, key=lambda x: (x[1].get("ntsl_pc") or 9_999_999, x[0]))
        return self._make_station(
            chrstn_mno=row["chrstn_mno"],
            name=row["chrstn_nm"],
            road=row.get("road_nm_addr") or row.get("lotno_addr"),
            dist=dist,
            ntsl_pc=row.get("ntsl_pc"),
            is_open=row.get("oper_yn") == "Y",
            wait=row.get("wait_vhcle_alge"),
            lat_=row["let"],
            lon_=row["lon"],
            avg_price=avg_price,
            min_price=min_price,
            realtime=row.get("rltm_info_yn") == "Y",
            fuel_percent=fuel_percent,
        )

    async def _fetch_station_by_python(
        self,
        candidates: list[tuple[float, object]],
        avg_price: float | None,
        min_price: float | None,
        fuel_percent: int,
    ) -> NearestRecommendationStation | None:
        """Python 폴백: 후보 중 최저가 1곳 선택 (candidates는 _load_priced_candidates 결과)."""
        if not candidates:
            return None

        dist, st = min(candidates, key=lambda x: (x[1].ntsl_pc, x[0]))
        latest = (
            await self.db.execute(
                select(HydrogenStationStatus)
                .where(HydrogenStationStatus.chrstn_mno == st.chrstn_mno)
                .order_by(
                    HydrogenStationStatus.last_mdfcn_dt.desc().nullslast(),
                    HydrogenStationStatus.status_id.desc(),
                )
                .limit(1)
            )
        ).scalar_one_or_none()

        return self._make_station(
            chrstn_mno=st.chrstn_mno,
            name=st.chrstn_nm,
            road=st.road_nm_addr or st.lotno_addr,
            dist=dist,
            ntsl_pc=st.ntsl_pc,
            is_open=st.oper_yn == "Y",
            wait=latest.wait_vhcle_alge if latest else None,
            lat_=st.let,
            lon_=st.lon,
            avg_price=avg_price,
            min_price=min_price,
            realtime=st.rltm_info_yn == "Y",
            fuel_percent=fuel_percent,
        )

    # ===== Insight 조립 =====

    def _build_insight(
        self,
        status: str,
        remaining_range: float,
        gemini: dict | None,
        driving_habit: DrivingHabit | None,
        no_station: bool = False,
    ) -> NearestRecommendationInsight:
        label, subtitle, fallback_timing = _FALLBACK_LABELS[status]
        g = gemini or {}
        habit_consumption, habit_tone = _consumption_from_habit(driving_habit)
        message = (
            NO_STATION_MESSAGE
            if no_station
            else g.get("message") or _fallback_message(status, remaining_range)
        )
        return NearestRecommendationInsight(
            status=status,
            status_label=g.get("status_label") or label,
            subtitle=g.get("subtitle") or subtitle,
            message=message,
            metrics=_metrics(
                remaining_range,
                g.get("charge_timing") or fallback_timing,
                g.get("consumption_value") or habit_consumption,
                g.get("consumption_tone") or habit_tone,
            ),
        )

    # ===== 메인 엔트리 =====

    async def get_nearest_cheapest(
        self,
        request: NearestRecommendationRequest,
    ) -> NearestRecommendationResponse:
        fuel_percent = request.vehicle.fuel_percent
        remaining_range = request.vehicle.remaining_range
        lat = request.location.let
        lon = request.location.lon
        radius_km = request.context.radius_km if request.context else 10.0
        driving_habit = request.driving_habit
        status = determine_status(fuel_percent)

        # 1. Gemini 단일 호출: SQL + insight 동시 생성
        gemini_data = None
        if self.ai_enabled and self.client:
            gemini_data = await self._call_gemini_combined(
                status, fuel_percent, remaining_range, lat, lon, radius_km, driving_habit
            )

        # 2. 반경 내 후보 + 평균가·최저가 한 번만 조회 (SQL price_diff / Python 폴백 공용)
        candidates, avg_price, min_price = await self._load_priced_candidates(
            lat, lon, radius_km
        )

        # 3. 충전소 조회: Gemini SQL 우선, 실패 시 Python 폴백
        station: NearestRecommendationStation | None = None
        if gemini_data and gemini_data.get("station_sql"):
            station = await self._fetch_station_by_sql(
                gemini_data["station_sql"], lat, lon, radius_km,
                fuel_percent, avg_price, min_price,
            )
        if station is None:
            station = await self._fetch_station_by_python(
                candidates, avg_price, min_price, fuel_percent
            )

        # 4. 응답 조립
        insight = self._build_insight(
            status, remaining_range, gemini_data, driving_habit, no_station=(station is None)
        )
        return NearestRecommendationResponse(
            screen=f"battery_{status}",
            vehicle=NearestRecommendationVehicleResponse(
                fuel_percent=fuel_percent,
                remaining_range=remaining_range,
                fuel_type=request.vehicle.fuel_type,
            ),
            ai_insight=insight,
            recommended_station=station,
        )
