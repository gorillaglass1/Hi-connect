"""nearest_recommendation Gemini 단일 호출 프롬프트 관리 모듈.

Gemini를 **1번만** 호출해 충전소 조회 SQL + ai_insight JSON을 함께 생성한다.
결과를 파싱한 뒤:
  - station_sql → validate → 실행 → 충전소 데이터 획득
  - 나머지 필드 → NearestRecommendationInsight 조립

구성:
- SYSTEM_INSTRUCTION: 모델 역할 + 출력 JSON 스키마 규칙 (고정)
- MESSAGE_STYLES: 호출마다 message 말투를 바꾸는 스타일 가이드
- GENERATION_TEMPERATURE: 표현 다양성 온도
- build_prompt(): 요청 데이터 전체를 받아 user 프롬프트 생성
"""
import json
import math
import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.schemas.nearest_recommendation_schema import DrivingHabit

GENERATION_TEMPERATURE = 1.2

# ===== DB 스키마 요약 =====
_DB_SCHEMA = """
테이블: hydrogen_stations
  chrstn_mno   VARCHAR(30) PK  충전소 관리번호
  chrstn_nm    VARCHAR(100)    충전소명
  road_nm_addr VARCHAR(255)    도로명 주소
  lotno_addr   VARCHAR(255)    지번 주소
  ntsl_pc      INTEGER         수소 판매 가격(원/kg), NULL=가격 미공개
  let          DECIMAL(17,14)  위도
  lon          DECIMAL(17,14)  경도
  oper_yn      CHAR(1)         운영 여부 'Y'=운영중
  del_at       CHAR(1)         삭제 여부 '0'=정상
  rltm_info_yn CHAR(1)         실시간 정보 제공 여부 'Y'=실시간

테이블: hydrogen_station_status
  status_id        INTEGER PK 자동증가
  chrstn_mno       VARCHAR(30) FK→hydrogen_stations
  wait_vhcle_alge  INTEGER     대기 차량 수(NULL=정보없음)
  last_mdfcn_dt    TIMESTAMP   최종 수정일시
"""

# ===== 시스템 인스트럭션 (단일 호출용) =====
SYSTEM_INSTRUCTION = f"""당신은 수소차 커넥티드 서비스의 AI 어시스턴트입니다.
아래 DB 스키마와 요청 데이터를 보고, 다음 두 가지를 **하나의 JSON 객체**로 출력하세요.

{_DB_SCHEMA}

출력 JSON 스키마 (이 형식 그대로, 다른 텍스트·마크다운·코드블록 없이):
{{
  "station_sql": "후보 충전소를 조회하는 PostgreSQL SELECT 쿼리 (문자열)",
  "status_label": "연료 상태 한글 라벨 (예: 수소 잔량 충분)",
  "subtitle": "카드 큰 제목 한 줄 (예: 지금 충전이 급하지 않아요)",
  "message": "개인화 안내 문구 1~2문장 (한국어 존댓말, 80자 이내)",
  "charge_timing": "권장 충전 시점 (10자 이내, 예: 약 2시간 후)",
  "consumption_value": "예상 소모율 (정상 / 다소 높음 / 낮음 중 하나)",
  "consumption_tone": "소모율 tone (neutral / warning / positive 중 하나)"
}}

station_sql 작성 규칙:
- SELECT 문만 허용 (INSERT/UPDATE/DELETE/DROP 등 금지)
- SQL 주석(--, /* */, #) 금지
- 세미콜론은 끝에만 한 번
- 반드시: oper_yn = 'Y' AND del_at = '0' AND ntsl_pc IS NOT NULL
- 주어진 위도·경도 바운딩 박스 범위 내에서 조회
- 각 충전소의 최신 상태는 LATERAL 서브쿼리로 LEFT JOIN
- SELECT 컬럼: s.chrstn_mno, s.chrstn_nm, s.road_nm_addr, s.lotno_addr,
    s.ntsl_pc, CAST(s.let AS FLOAT8) AS let, CAST(s.lon AS FLOAT8) AS lon,
    s.oper_yn, s.rltm_info_yn, st.wait_vhcle_alge
- 정렬: 거리 근사값 ASC, ntsl_pc ASC / LIMIT 5

운전습관 반영 가이드:
- style = "aggressive" 또는 events_per_hour >= 2.0:
    consumption_value="다소 높음", consumption_tone="warning", charge_timing 앞당기기
    message에 연료 소모 성향 자연스럽게 반영
- style = "calm":
    consumption_value="낮음", consumption_tone="positive", 가격·거리 효율 강조
- style = "moderate" 또는 운전습관 없음:
    consumption_value="정상", consumption_tone="neutral", 균형 잡힌 안내

연료 상태(status)별 안내 톤:
- sufficient: 여유 있는 긍정적 톤
- recommend: 슬슬 준비 권장, 부드러운 독려
- urgent: 즉시 충전 강조 (패닉 없이)

message에 수소차 오너에게 실용적인 깨알 정보(충전팁·관리팁)를 자연스럽게 한 문장 안에 포함하세요.
제공된 데이터에만 근거하고 없는 정보를 지어내지 마세요.
"""

# ===== message 말투 다양성 =====
MESSAGE_STYLES = [
    "가격 이점을 자연스럽게 강조하는 정보형 말투",
    "운전자를 가볍게 격려하는 따뜻한 말투",
    "핵심만 짚어 주는 간결하고 단정적인 말투",
    "거리·대기 등 편의를 부각하는 친근한 권유형 말투",
    "주행가능거리 같은 수치를 곁들인 데이터 강조형 말투",
    "다정하게 안부를 건네듯 부드러운 말투",
    "지금 행동을 가볍게 제안하는 코치 같은 말투",
]


def _pick_style(rng: random.Random | None = None) -> str:
    return (rng or random).choice(MESSAGE_STYLES)


def _driving_habit_section(driving_habit: "DrivingHabit | None") -> str:
    if driving_habit is None:
        return ""
    style_desc = {
        "calm": "안전 운전 (급가속/급정거 거의 없음)",
        "moderate": "보통 (급가속/급정거 다소 있음)",
        "aggressive": "공격적 운전 (급가속/급정거 잦음)",
        "unknown": "알 수 없음",
    }.get(driving_habit.style, "알 수 없음")
    return (
        "\n운전습관:\n"
        + json.dumps(
            {
                "누적_세션_수": driving_habit.total_sessions,
                "누적_주행_시간_분": driving_habit.total_driving_minutes,
                "급가속_횟수": driving_habit.harsh_accel_count,
                "급정거_횟수": driving_habit.harsh_brake_count,
                "부주의_횟수": driving_habit.incautious_count,
                "평균_점수": driving_habit.avg_score,
                "운전_스타일": f"{driving_habit.style} ({style_desc})",
                "시간당_위험이벤트": driving_habit.events_per_hour,
            },
            ensure_ascii=False,
        )
        + "\n"
    )


def build_prompt(
    status: str,
    fuel_percent: int,
    remaining_range: float,
    lat: float,
    lon: float,
    radius_km: float,
    driving_habit: "DrivingHabit | None" = None,
    style: str | None = None,
) -> str:
    """단일 Gemini 호출용 user 프롬프트: SQL + insight 동시 생성."""
    if style is None:
        style = _pick_style()

    delta_lat = radius_km / 111.0
    delta_lon = radius_km / (111.0 * math.cos(math.radians(lat)))
    lat_min = round(lat - delta_lat, 6)
    lat_max = round(lat + delta_lat, 6)
    lon_min = round(lon - delta_lon, 6)
    lon_max = round(lon + delta_lon, 6)

    request_data = {
        "연료_상태": status,
        "연료_잔량_%": fuel_percent,
        "주행가능거리_km": remaining_range,
        "현재_위도": lat,
        "현재_경도": lon,
        "검색_반경_km": radius_km,
        "바운딩박스_위도": [lat_min, lat_max],
        "바운딩박스_경도": [lon_min, lon_max],
        "거리_근사_정렬식": f"(CAST(s.let AS FLOAT8) - {lat})^2 + (CAST(s.lon AS FLOAT8) - {lon})^2",
    }

    return (
        f"요청 데이터:\n{json.dumps(request_data, ensure_ascii=False)}"
        f"{_driving_habit_section(driving_habit)}\n"
        f"message 말투: {style}\n\n"
        "위 데이터를 바탕으로 station_sql과 ai_insight 필드를 담은 JSON 하나를 출력하세요."
    )
