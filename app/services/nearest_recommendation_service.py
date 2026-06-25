import asyncio
import logging
import json
import os
import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import is_dashboard_ai_enabled
from app.models.hydrogen_station_status import HydrogenStationStatus
from app.repositories import hydrogen_station_repo
from app.services import nearest_recommendation_prompt as prompt_manager
from app.schemas.nearest_recommendation_schema import (
    NearestRecommendationInsight,
    NearestRecommendationMetric,
    NearestRecommendationRequest,
    NearestRecommendationResponse,
    NearestRecommendationStation,
    NearestRecommendationVehicleResponse,
)
# 거리 계산은 기존 추천 로직의 haversine_distance를 재사용 (새로 만들지 않음)
from app.services.recommendation_service import haversine_distance

logger = logging.getLogger("nearest_recommendation_service")

# google-genai 사용 패턴은 recommendation_reason_service 를 그대로 따른다.
try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:  # pragma: no cover
    HAS_GENAI = False

GEMINI_MODEL = "gemini-2.5-flash"

# Gemini 호출 타임아웃(초). 응답이 느릴 수 있어 여유 있게 설정한다.
# SDK HTTP 타임아웃(client http_options)과 asyncio 대기 타임아웃에 함께 사용한다.
GEMINI_TIMEOUT_SECONDS = 60.0

# ===== 임계값/상수 =====
TANK_CAPACITY_KG = 6.33            # NEXO 기준, 추후 SDK/차종 값으로 교체 예정
FUEL_SUFFICIENT_THRESHOLD = 50     # 이상이면 sufficient
FUEL_RECOMMEND_THRESHOLD = 25      # 이상이면 recommend, 미만은 urgent

# status별 한글 라벨 / 부제목 / 권장 충전 시점 문구 (추후 LLM 교체 시 참고용 고정 템플릿)
STATUS_LABELS = {
    "sufficient": "충분",
    "recommend": "충전 권장",
    "urgent": "긴급",
}
STATUS_SUBTITLES = {
    "sufficient": "잔량 충분",
    "recommend": "충전 권장 구간",
    "urgent": "긴급 충전 필요",
}
STATUS_CHARGE_TIMING = {
    "sufficient": "여유 있음",
    "recommend": "곧 충전 권장",
    "urgent": "즉시 충전",
}

# 평균 소모율 지표 표시값 (추후 실데이터 연동 시 교체 예정, 현재는 고정값)
AVERAGE_CONSUMPTION_LABEL = "정상"

# radius 내 가격 있는 충전소가 0개일 때 안내 메시지
NO_STATION_MESSAGE = "근처에 충전소 정보가 없어요. 잠시 후 다시 시도해 주세요."


def determine_status(fuel_percent: int) -> str:
    """연료 잔량(%) 기준 규칙 판정 (LLM 미사용)."""
    if fuel_percent >= FUEL_SUFFICIENT_THRESHOLD:
        return "sufficient"
    if fuel_percent >= FUEL_RECOMMEND_THRESHOLD:
        return "recommend"
    return "urgent"


def calculate_charge_amount(fuel_percent: int) -> float:
    """가득 채우기까지 필요한 충전량(kg)."""
    return TANK_CAPACITY_KG * (1 - fuel_percent / 100)


def calculate_estimated_cost(fuel_percent: int, price: int) -> int:
    """예상 충전 비용(원) = 충전량(kg) * 판매가(원/kg)."""
    return round(calculate_charge_amount(fuel_percent) * price)


def generate_insight_message(status: str, remaining_range: float) -> str:
    """status별 고정 템플릿 인사이트 메시지 (추후 LLM 교체 예정)."""
    if status == "sufficient":
        return f"잔량이 넉넉해요. 약 {remaining_range}km 더 주행할 수 있어요."
    if status == "recommend":
        return f"슬슬 충전을 준비하세요. 약 {remaining_range}km 주행 가능해요."
    return f"지금 충전이 필요해요. 남은 주행가능거리는 약 {remaining_range}km예요."


def _build_metrics(
    status: str,
    remaining_range: float,
    charge_timing: str | None = None,
) -> list[NearestRecommendationMetric]:
    """표시용 지표 목록: 주행가능거리 / 권장 충전 시점 / 평균 소모율.

    charge_timing 이 주어지면(예: Gemini 생성값) 권장 충전 시점에 사용하고,
    없으면 status별 고정 템플릿(STATUS_CHARGE_TIMING)으로 폴백한다.
    """
    return [
        NearestRecommendationMetric(
            label="주행가능거리",
            value=str(remaining_range),
            unit="km",
        ),
        NearestRecommendationMetric(
            label="권장 충전 시점",
            value=charge_timing or STATUS_CHARGE_TIMING[status],
        ),
        NearestRecommendationMetric(
            label="평균 소모율",
            value=AVERAGE_CONSUMPTION_LABEL,
        ),
    ]


class NearestRecommendationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        # ai_insight.message 를 Gemini 로 생성할지 스위치. DASHBOARD_AI_ENABLED 공유(기본 True).
        self.ai_enabled = is_dashboard_ai_enabled()
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.client = None
        if self.ai_enabled and HAS_GENAI and self.api_key:
            try:
                # http_options.timeout 은 밀리초 단위. API 응답이 느려도 끊기지 않도록
                # SDK HTTP 타임아웃도 여유 있게 잡는다.
                self.client = genai.Client(
                    api_key=self.api_key,
                    http_options=types.HttpOptions(
                        timeout=int(GEMINI_TIMEOUT_SECONDS * 1000)
                    ),
                )
            except Exception as e:  # pragma: no cover - defensive
                logger.error(f"Failed to initialize Gemini Client: {e}")

    async def _get_latest_status(self, chrstn_mno: str) -> HydrogenStationStatus | None:
        """충전소 최신 상태 1건 (repo 패턴 동일: last_mdfcn_dt desc, status_id desc top1)."""
        result = await self.db.execute(
            select(HydrogenStationStatus)
            .where(HydrogenStationStatus.chrstn_mno == chrstn_mno)
            .order_by(
                HydrogenStationStatus.last_mdfcn_dt.desc().nullslast(),
                HydrogenStationStatus.status_id.desc(),
            )
            .limit(1)
        )
        return result.scalar_one_or_none()

    def _build_insight(
        self,
        status: str,
        remaining_range: float,
        message: str | None = None,
        charge_timing: str | None = None,
    ) -> NearestRecommendationInsight:
        return NearestRecommendationInsight(
            status=status,
            status_label=STATUS_LABELS[status],
            subtitle=STATUS_SUBTITLES[status],
            message=message or generate_insight_message(status, remaining_range),
            metrics=_build_metrics(status, remaining_range, charge_timing),
        )

    async def _resolve_ai_insight(
        self,
        status: str,
        remaining_range: float,
        station: NearestRecommendationStation,
    ) -> tuple[str, str]:
        """확정된 추천 충전소 값으로 권장 충전 시점과 ai_insight.message 를 함께 생성한다.

        반환값은 (권장_충전_시점, message) 튜플이다. 스위치 off / client 미설정 /
        호출 예외 / 타임아웃 / 파싱 실패 시 기존 고정 템플릿으로 폴백한다.
        (충전소 선택은 하지 않음)
        """
        fallback_timing = STATUS_CHARGE_TIMING[status]
        fallback_message = generate_insight_message(status, remaining_range)

        if not self.ai_enabled or not self.client:
            return fallback_timing, fallback_message

        # SDK 호출은 동기 블로킹이므로 별도 스레드에서 실행하고, 응답이 느려도
        # 끊기지 않도록 여유 있는 타임아웃(GEMINI_TIMEOUT_SECONDS)을 둔다.
        try:
            raw_text = await asyncio.wait_for(
                asyncio.to_thread(
                    self._call_gemini, status, remaining_range, station
                ),
                timeout=GEMINI_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            logger.warning(
                f"Gemini insight generation timed out after "
                f"{GEMINI_TIMEOUT_SECONDS}s, falling back"
            )
            return fallback_timing, fallback_message
        except Exception as e:
            logger.error(f"Gemini insight generation failed, falling back: {e}")
            return fallback_timing, fallback_message

        parsed = self._parse_insight(raw_text)
        if not parsed:
            return fallback_timing, fallback_message

        timing = parsed.get("charge_timing") or fallback_timing
        message = parsed.get("message") or fallback_message
        return timing, message

    def _call_gemini(
        self,
        status: str,
        remaining_range: float,
        station: NearestRecommendationStation,
    ) -> str | None:
        station_facts = {
            "연료_상태": status,
            "주행가능거리_km": remaining_range,
            "충전소명": station.name,
            "거리_km": station.distance_km,
            "판매가격_원_per_kg": station.ntsl_pc,
            "평균대비_가격차": station.price_diff_from_avg,
            "예상_충전비용_원": station.estimated_cost,
            "대기차량_대수": station.wait_vhcle_alge,
            "운영중": station.is_open,
        }

        # 프롬프트 관리 모듈에서 고정 system instruction + 호출마다 바뀌는 스타일을
        # 가져와 다양한 문구가 나오도록 한다. (자세한 규칙/스타일은 prompt_manager 참고)
        user_prompt = prompt_manager.build_user_prompt(station_facts)

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
    def _parse_insight(raw_text: str | None) -> dict | None:
        """Gemini 응답에서 charge_timing/message 를 추출한다. 실패 시 None."""
        if not raw_text:
            return None
        cleaned = re.sub(r"```(?:json)?\s*", "", raw_text, flags=re.IGNORECASE)
        cleaned = cleaned.replace("```", "").strip()
        try:
            parsed = json.loads(cleaned)
        except (json.JSONDecodeError, ValueError):
            return None
        if not isinstance(parsed, dict):
            return None

        result: dict[str, str] = {}
        timing = parsed.get("charge_timing")
        if isinstance(timing, str) and timing.strip():
            result["charge_timing"] = timing.strip()
        message = parsed.get("message")
        if isinstance(message, str) and message.strip():
            result["message"] = message.strip()
        return result or None

    async def get_nearest_cheapest(
        self,
        request: NearestRecommendationRequest,
    ) -> NearestRecommendationResponse:
        fuel_percent = request.vehicle.fuel_percent
        remaining_range = request.vehicle.remaining_range
        cur_lat = request.location.let
        cur_lon = request.location.lon
        radius_km = request.context.radius_km if request.context else 10.0

        status = determine_status(fuel_percent)

        # 1. 활성 충전소 조회 (oper_yn='Y' AND del_at='0') — 기존 repo 재사용
        stations = (
            await hydrogen_station_repo.get_active_hydrogen_stations_for_recommendation(
                self.db
            )
        )

        # 2. location(let/lon) 기준 거리 계산 → radius_km 이내 필터
        radius_candidates = []
        for st in stations:
            if st.let is None or st.lon is None:
                continue
            st_lat = float(st.let)
            st_lon = float(st.lon)
            dist = haversine_distance(cur_lat, cur_lon, st_lat, st_lon)
            if dist > radius_km:
                continue
            radius_candidates.append({
                "model": st,
                "lat": st_lat,
                "lon": st_lon,
                "distance_km": dist,
            })

        # 3. 가격(ntsl_pc) 있는 후보만 최저가 대상 → 0개면 빈 응답
        priced_candidates = [
            c for c in radius_candidates if c["model"].ntsl_pc is not None
        ]
        if not priced_candidates:
            return NearestRecommendationResponse(
                screen=f"battery_{status}",
                vehicle=NearestRecommendationVehicleResponse(
                    fuel_percent=fuel_percent,
                    remaining_range=remaining_range,
                    fuel_type=request.vehicle.fuel_type,
                ),
                ai_insight=self._build_insight(
                    status, remaining_range, message=NO_STATION_MESSAGE
                ),
                recommended_station=None,
            )

        # ntsl_pc 오름차순 → 최저가 1곳
        priced_candidates.sort(key=lambda c: c["model"].ntsl_pc)
        cheapest = priced_candidates[0]
        station = cheapest["model"]

        # 4. 최신 상태 1건 → 대기차량 추출
        latest_status = await self._get_latest_status(station.chrstn_mno)
        wait_vhcle_alge = latest_status.wait_vhcle_alge if latest_status else None

        # 6. 예상 충전 비용
        estimated_cost = calculate_estimated_cost(fuel_percent, station.ntsl_pc)

        # 7. 반경 내 가격 있는 충전소 평균 대비 가격 차이 (음수면 평균보다 저렴)
        avg_price = sum(c["model"].ntsl_pc for c in priced_candidates) / len(
            priced_candidates
        )
        price_diff_from_avg = round(station.ntsl_pc - avg_price, 1)

        recommended_station = NearestRecommendationStation(
            chrstn_mno=station.chrstn_mno,
            name=station.chrstn_nm,
            road_nm_addr=station.road_nm_addr or station.lotno_addr,
            distance_km=round(cheapest["distance_km"], 2),
            ntsl_pc=station.ntsl_pc,
            price_diff_from_avg=price_diff_from_avg,
            estimated_cost=estimated_cost,
            wait_vhcle_alge=wait_vhcle_alge,
            is_open=station.oper_yn == "Y",
            let=cheapest["lat"],
            lon=cheapest["lon"],
        )

        # 8. 권장 충전 시점 + ai_insight.message 생성 (Gemini, 실패 시 고정 템플릿 폴백)
        ai_charge_timing, ai_message = await self._resolve_ai_insight(
            status, remaining_range, recommended_station
        )

        # 9. 응답 조립
        return NearestRecommendationResponse(
            screen=f"battery_{status}",
            vehicle=NearestRecommendationVehicleResponse(
                fuel_percent=fuel_percent,
                remaining_range=remaining_range,
                fuel_type=request.vehicle.fuel_type,
            ),
            ai_insight=self._build_insight(
                status,
                remaining_range,
                message=ai_message,
                charge_timing=ai_charge_timing,
            ),
            recommended_station=recommended_station,
        )
