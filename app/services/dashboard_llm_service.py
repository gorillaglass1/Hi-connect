"""대시보드 통합 인사이트를 위한 단일 LLM(Gemini) 호출.

설계:
- 호출은 요청당 1회. [수집 컨텍스트 + DB 스키마 + 검수 팁 카탈로그]를 프롬프트에
  넣고, 정해진 JSON만 출력하게 한다.
- 8초 타임아웃. 실패/타임아웃/파싱 실패 시 None 을 반환해 백엔드가 폴백한다.
- 기존 recommendation_reason_service 의 google-genai 사용 패턴을 그대로 따른다.
"""

import asyncio
import json
import logging
import os
import re
from dataclasses import dataclass

from app.core.config import is_dashboard_ai_enabled

logger = logging.getLogger("dashboard_llm_service")

try:
    from google import genai
    HAS_GENAI = True
except ImportError:  # pragma: no cover
    HAS_GENAI = False

GEMINI_MODEL = "gemini-flash-lite-latest"
LLM_TIMEOUT_SECONDS = 25.0

# LLM에 알려줄 충전소 스키마 요약. ID는 문자열 chrstn_mno, 좌표는 lon(경도)/let(위도).
_DB_SCHEMA_HINT = """테이블: hydrogen_stations
- chrstn_mno (TEXT): 충전소 관리번호 (기본키, 문자열 ID)
- chrstn_nm (TEXT): 충전소명
- road_nm_addr (TEXT): 도로명 주소
- lon (NUMERIC): 경도(longitude)
- let (NUMERIC): 위도(latitude)  ← 주의: let 이 위도임
- oper_yn (CHAR): 운영 여부 'Y'/'N'
- del_at (CHAR): 삭제 여부 ('0'=정상)"""


@dataclass
class LlmInsight:
    """LLM이 반환한 원시 인사이트(검증 전)."""

    station_sql: str
    condition: dict
    hydrogen_tip: dict


class DashboardLlmService:
    def __init__(self):
        # 대시보드 전용 스위치. 충전소 추천(AI_REASON_ENABLED)과 분리되어 있다.
        self.ai_enabled = is_dashboard_ai_enabled()
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.client = None
        if self.ai_enabled and HAS_GENAI and self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as exc:  # pragma: no cover - 방어적
                logger.error("Gemini Client 초기화 실패: %s", exc)

    async def generate(
        self, context: dict, tip_catalog: list[dict]
    ) -> LlmInsight | None:
        """단일 LLM 호출. 실패/타임아웃/파싱 실패 시 None."""
        if not self.client:
            logger.info("Gemini 미설정. LLM 인사이트 없이 폴백합니다.")
            return None

        prompt = self._build_prompt(context, tip_catalog)
        try:
            raw_text = await asyncio.wait_for(
                asyncio.to_thread(self._call_model, prompt),
                timeout=LLM_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            logger.warning("LLM 호출 %.1f초 타임아웃, 폴백합니다.", LLM_TIMEOUT_SECONDS)
            return None
        except Exception as exc:
            logger.error("LLM 호출 실패, 폴백합니다: %s", exc)
            return None

        return self._parse(raw_text)

    def _call_model(self, prompt: str) -> str | None:
        response = self.client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )
        return response.text

    @staticmethod
    def _build_prompt(context: dict, tip_catalog: list[dict]) -> str:
        return f"""당신은 수소전기차 대시보드의 인사이트 생성기입니다.
아래 컨텍스트를 바탕으로 아래 JSON 객체 하나만 출력하세요.
설명, 마크다운, 코드블록(```) 없이 순수 JSON만 출력합니다.

[수집 컨텍스트]
{json.dumps(context, ensure_ascii=False)}

[DB 스키마]
{_DB_SCHEMA_HINT}

[검수된 수소 팁 카탈로그] (tip_id 는 반드시 이 목록 중 하나만 선택)
{json.dumps(tip_catalog, ensure_ascii=False)}

규칙:
- station_sql: 운영 중인 충전소를 조회하는 "단일 SELECT 문" 하나.
  * 반드시 chrstn_mno, chrstn_nm, lon, let 컬럼을 SELECT 에 포함.
  * oper_yn='Y' AND del_at='0' 조건을 포함.
  * 거리 계산/정렬을 SQL 에서 하지 말 것 (백엔드가 haversine 으로 처리).
  * INSERT/UPDATE/DELETE/DROP 등 변경 구문 금지, 세미콜론 1개 이하.
- condition: 오늘의 운전 컨디션.
  * score 는 0~100 정수, grade 는 "좋음"/"주의"/"나쁨" 중 하나.
  * briefing 은 40자 이내의 한국어 운전 조언.
- hydrogen_tip: 위 카탈로그에서 컨텍스트에 가장 맞는 tip_id 하나를 선택.
  * 팁 본문은 작성하지 말 것 (백엔드가 채움). tip_id 와 짧은 맥락만 제공.
  * context_label 예: "기온 -2°C 감지", reason 예: "오늘 날씨에 맞춰 추천".

출력 형식(JSON):
{{
  "station_sql": "SELECT chrstn_mno, chrstn_nm, lon, let FROM hydrogen_stations WHERE oper_yn='Y' AND del_at='0'",
  "condition": {{"score": 0, "grade": "좋음", "briefing": "..."}},
  "hydrogen_tip": {{"tip_id": "...", "context_label": "...", "reason": "..."}}
}}"""

    @staticmethod
    def _parse(raw_text: str | None) -> LlmInsight | None:
        if not raw_text:
            return None
        cleaned = re.sub(r"```(?:json)?\s*", "", raw_text, flags=re.IGNORECASE)
        cleaned = cleaned.replace("```", "").strip()
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            cleaned = cleaned[start : end + 1]
        try:
            parsed = json.loads(cleaned)
        except (json.JSONDecodeError, ValueError):
            logger.warning("LLM JSON 파싱 실패, 폴백합니다.")
            return None
        if not isinstance(parsed, dict):
            return None

        station_sql = parsed.get("station_sql")
        condition = parsed.get("condition")
        hydrogen_tip = parsed.get("hydrogen_tip")
        if not isinstance(station_sql, str):
            station_sql = ""
        if not isinstance(condition, dict):
            condition = {}
        if not isinstance(hydrogen_tip, dict):
            hydrogen_tip = {}
        return LlmInsight(
            station_sql=station_sql,
            condition=condition,
            hydrogen_tip=hydrogen_tip,
        )
