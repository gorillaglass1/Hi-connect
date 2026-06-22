import json
import logging
import os
import re
from dataclasses import dataclass, field

from app.core.config import is_ai_reason_enabled

logger = logging.getLogger("recommendation_reason_service")

# Try importing the modern google-genai library
try:
    from google import genai
    HAS_GENAI = True
except ImportError:  # pragma: no cover
    HAS_GENAI = False

GEMINI_MODEL = "gemini-2.5-flash"


@dataclass
class RecommendationWeights:
    price: float
    wait: float
    distance: float
    facilities: float


@dataclass
class StationReasonFacts:
    """단일 충전소의 추천 사유 생성을 위한 사실 데이터."""

    chrstn_nm: str
    price_val: float
    min_price: float
    detour_distance: float
    distance_to_station: float
    service_available: bool
    wait_time_minutes: int
    queue_reasons: list[str] = field(default_factory=list)
    facility_count: int = 0
    active_facilities: list[str] = field(default_factory=list)
    is_reachable: bool = True
    # False일 때는 목적지가 없어 현위치 근처 추천 모드임을 의미한다.
    has_destination: bool = True


class RecommendationReasonService:
    """충전소별 추천 사유 메시지를 생성한다.

    추천 사유 문구만 Gemini API로 한 번에(배치) 생성하며, 키가 없거나 호출이
    실패하면 결정적인 규칙 기반 문구로 폴백한다.
    """

    def __init__(self):
        # 서버 메인 설정(.env)의 AI_REASON_ENABLED 스위치. 기본 False(규칙 기반).
        self.ai_enabled = is_ai_reason_enabled()
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.client = None
        if self.ai_enabled and HAS_GENAI and self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:  # pragma: no cover - defensive
                logger.error(f"Failed to initialize Gemini Client: {e}")

    def build_rule_based_reason(
        self,
        facts: StationReasonFacts,
        weights: RecommendationWeights,
    ) -> str:
        """기존 규칙 기반 추천 사유 문구. Gemini 폴백으로도 사용된다."""
        reasons: list[str] = []
        if weights.distance >= 1.5:
            if facts.has_destination and facts.detour_distance <= 2.0:
                reasons.append("우회 거리가 최소화된 최적 경로 상에 있습니다.")
            elif not facts.has_destination and facts.distance_to_station <= 3.0:
                reasons.append(
                    f"현재 위치에서 약 {facts.distance_to_station}km로 가깝습니다."
                )
        if weights.price >= 1.5 and facts.price_val <= facts.min_price + 300:
            reasons.append("판매 가격이 저렴하여 경제적입니다.")
        if not facts.service_available:
            reasons.append("현재 운영/압력 상태가 좋지 않아 추천 우선순위를 낮췄습니다.")
        elif weights.wait >= 1.5 and facts.wait_time_minutes <= 8:
            reasons.append(f"예상 대기시간이 약 {facts.wait_time_minutes}분으로 짧습니다.")
        elif weights.wait >= 1.5 and facts.queue_reasons:
            reasons.append(facts.queue_reasons[0])
        if weights.facilities >= 1.5 and facts.facility_count >= 2:
            reasons.append(
                f"주변 편의시설({', '.join(facts.active_facilities[:2])})이 잘 구비되어 있습니다."
            )

        if not reasons:
            if facts.is_reachable:
                reasons.append("사용자 가중치 분석 결과 전반적 매칭도가 매우 높습니다.")
            else:
                reasons.append("현재 주행가능거리를 초과하여 경로 충전소로 도달이 불가능할 수 있습니다.")

        return " ".join(reasons)

    async def generate_reasons(
        self,
        stations: list[StationReasonFacts],
        weights: RecommendationWeights,
    ) -> list[str]:
        """충전소별 추천 사유 리스트를 입력 순서대로 반환한다."""
        fallback = [self.build_rule_based_reason(facts, weights) for facts in stations]

        if not stations or not self.ai_enabled or not self.client:
            if stations and self.ai_enabled and not self.client:
                logger.info(
                    "Gemini client unavailable. Using rule-based recommendation reasons."
                )
            return fallback

        try:
            ai_reasons = self._generate_with_gemini(stations, weights)
        except Exception as e:
            logger.error(f"Gemini reason generation failed, falling back: {e}")
            return fallback

        if not ai_reasons or len(ai_reasons) != len(stations):
            logger.warning(
                "Gemini returned %s reasons for %s stations. Falling back.",
                len(ai_reasons) if ai_reasons else 0,
                len(stations),
            )
            return fallback

        # 개별 항목이 비어 있으면 해당 충전소만 규칙 기반 문구로 보완.
        return [
            ai.strip() if isinstance(ai, str) and ai.strip() else fb
            for ai, fb in zip(ai_reasons, fallback)
        ]

    def _generate_with_gemini(
        self,
        stations: list[StationReasonFacts],
        weights: RecommendationWeights,
    ) -> list[str] | None:
        station_payload = [
            {
                "index": idx,
                "충전소명": facts.chrstn_nm,
                "판매가격": facts.price_val,
                "후보_최저가격": facts.min_price,
                "목적지_지정": facts.has_destination,
                "우회거리_km": round(facts.detour_distance, 2),
                "현위치_거리_km": round(facts.distance_to_station, 2),
                "운영_가능": facts.service_available,
                "예상_대기시간_분": facts.wait_time_minutes,
                "대기_분석_메모": facts.queue_reasons,
                "편의시설_수": facts.facility_count,
                "편의시설": facts.active_facilities,
                "도달_가능": facts.is_reachable,
            }
            for idx, facts in enumerate(stations)
        ]

        prompt = f"""당신은 수소충전소 추천 서비스의 안내 문구 작성 도우미입니다.
아래 사용자 가중치와 각 충전소의 사실 데이터를 바탕으로, 충전소마다 추천 이유를
1~2문장의 자연스러운 한국어 메시지로 작성하세요.

규칙:
- 제공된 사실 데이터에 근거해서만 작성하고, 없는 정보를 지어내지 마세요.
- 가중치가 높은 항목(가격/대기시간/거리/편의시설)을 우선해서 강조하세요.
- "운영_가능"이 false이면 현재 이용이 어려울 수 있음을 부드럽게 안내하세요.
- "도달_가능"이 false이면 주행가능거리를 초과할 수 있음을 안내하세요.
- "목적지_지정"이 false이면 목적지가 없는 상황이므로 우회거리 대신 현위치_거리_km(가까움)를 기준으로 안내하고, "경로 상" 같은 표현은 쓰지 마세요.
- 각 메시지는 80자 이내로 간결하게 작성하세요.

사용자 가중치(클수록 중요):
- 가격: {weights.price}
- 대기시간: {weights.wait}
- 거리: {weights.distance}
- 편의시설: {weights.facilities}

충전소 데이터(JSON):
{json.dumps(station_payload, ensure_ascii=False)}

출력 형식:
- 다른 설명 없이 JSON 배열만 출력하세요.
- 배열의 각 원소는 입력 index 순서와 동일한 추천 이유 문자열입니다.
- 예: ["이유1", "이유2"]
"""

        response = self.client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )
        return self._parse_reason_array(response.text)

    @staticmethod
    def _parse_reason_array(raw_text: str | None) -> list[str] | None:
        if not raw_text:
            return None
        cleaned = re.sub(r"```(?:json)?\s*", "", raw_text, flags=re.IGNORECASE)
        cleaned = cleaned.replace("```", "").strip()
        # 텍스트 앞뒤에 군더더기가 있을 경우 첫 배열만 추출.
        start = cleaned.find("[")
        end = cleaned.rfind("]")
        if start != -1 and end != -1 and end > start:
            cleaned = cleaned[start : end + 1]
        try:
            parsed = json.loads(cleaned)
        except (json.JSONDecodeError, ValueError):
            return None
        if not isinstance(parsed, list):
            return None
        return [str(item) for item in parsed]
