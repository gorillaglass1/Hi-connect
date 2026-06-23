"""대시보드 통합 인사이트 응답 스키마."""

from typing import Literal

from pydantic import BaseModel, Field


class ConditionInsight(BaseModel):
    """오늘의 운전 컨디션 점수/등급/브리핑. LLM 결과를 그대로 담는다."""

    score: int = Field(..., ge=0, le=100, description="운전 컨디션 점수 (0~100)")
    grade: Literal["좋음", "주의", "나쁨"] = Field(..., description="컨디션 등급")
    briefing: str = Field(..., description="40자 이내 운전 조언")


class HydrogenTipInsight(BaseModel):
    """수소 팁. 본문(tip)은 검수 풀에서, 라벨/근거는 LLM에서 온다."""

    tip: str = Field(..., description="검수 풀의 팁 본문 (LLM이 생성하지 않음)")
    context_label: str = Field(..., description="추천 맥락 라벨 (예: '기온 -2°C 감지')")
    reason: str = Field(..., description="추천 사유 (예: '오늘 날씨에 맞춰 추천')")


class Co2Insight(BaseModel):
    saved_kg: float = Field(..., description="절감한 CO2 (kg)")
    trees_equiv: float = Field(..., description="나무 환산 그루 수")


class NearestStationInsight(BaseModel):
    chrstn_mno: str = Field(..., description="충전소 관리번호 (문자열 ID)")
    name: str = Field(..., description="충전소명")
    distance_km: float = Field(..., description="현재 위치로부터의 거리 (km, 백엔드 haversine 계산)")
    status: str | None = Field(default=None, description="운영 상태")
    congestion: str | None = Field(default=None, description="혼잡도 (현재 미제공: null)")


class DashboardResponse(BaseModel):
    """대시보드 단일 통합 응답.

    condition / hydrogen_tip 은 LLM 실패 시 null 가능.
    co2 / nearest_station 은 백엔드만으로 계산 가능하므로 항상 채운다
    (단, 운영 중 충전소가 하나도 없으면 nearest_station 은 null).
    """

    condition: ConditionInsight | None = Field(default=None)
    hydrogen_tip: HydrogenTipInsight | None = Field(default=None)
    co2: Co2Insight
    nearest_station: NearestStationInsight | None = Field(default=None)
