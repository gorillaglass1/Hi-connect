from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


# ===== 요청 스키마 =====
class NearestRecommendationVehicle(BaseModel):
    fuel_percent: int = Field(..., description="현재 연료 잔량 (%)")
    remaining_range: float = Field(..., description="현재 차량 주행가능거리 (km)")
    fuel_type: str = Field(default="hydrogen", description="연료 종류")


class NearestRecommendationLocation(BaseModel):
    let: float = Field(..., description="현재 위치 위도 (DB 컬럼명 통일)")
    lon: float = Field(..., description="현재 위치 경도")


class NearestRecommendationContext(BaseModel):
    radius_km: float = Field(default=10.0, description="검색 반경 (km)")


class DrivingHabit(BaseModel):
    """클라이언트가 로컬에 누적한 운전습관 요약. 없으면 요청에서 키 자체가 생략된다."""
    total_sessions: int = Field(..., description="누적 주행 세션 수")
    total_driving_minutes: int = Field(..., description="누적 주행 시간 (분)")
    harsh_accel_count: int = Field(..., description="급가속 횟수")
    harsh_brake_count: int = Field(..., description="급정거 횟수")
    incautious_count: int = Field(..., description="부주의 (조향각 급변) 횟수")
    avg_score: int = Field(..., description="세션 평균 점수 (0~100)")
    style: Literal["calm", "moderate", "aggressive", "unknown"] = Field(
        ..., description="운전 스타일"
    )
    events_per_hour: float = Field(..., description="주행 1시간당 위험 이벤트 빈도")


class NearestRecommendationRequest(BaseModel):
    vehicle: NearestRecommendationVehicle = Field(..., description="차량 정보")
    location: NearestRecommendationLocation = Field(..., description="현재 위치")
    context: NearestRecommendationContext | None = Field(
        default=None, description="검색 컨텍스트 (선택)"
    )
    driving_habit: DrivingHabit | None = Field(
        default=None, description="누적 운전습관 (기록 없으면 생략)"
    )


# ===== 응답 스키마 =====
class NearestRecommendationVehicleResponse(BaseModel):
    fuel_percent: int = Field(..., description="현재 연료 잔량 (%)")
    remaining_range: float = Field(..., description="현재 차량 주행가능거리 (km)")
    fuel_type: str = Field(..., description="연료 종류")

    model_config = ConfigDict(from_attributes=True)


class NearestRecommendationMetric(BaseModel):
    label: str = Field(..., description="지표 이름")
    value: str = Field(..., description="지표 값 (표시용 문자열)")
    unit: str | None = Field(default=None, description="지표 단위")
    tone: Literal["positive", "warning", "neutral"] = Field(
        default="neutral", description="값 강조색 (positive/warning/neutral)"
    )

    model_config = ConfigDict(from_attributes=True)


class NearestRecommendationInsight(BaseModel):
    status: str = Field(..., description="연료 상태 (sufficient/recommend/urgent)")
    status_label: str = Field(..., description="연료 상태 한글 라벨")
    subtitle: str = Field(..., description="인사이트 부제목")
    message: str = Field(..., description="인사이트 메시지 (추후 LLM 교체 예정)")
    metrics: list[NearestRecommendationMetric] = Field(
        default_factory=list, description="표시용 지표 목록"
    )

    model_config = ConfigDict(from_attributes=True)


class NearestRecommendationStation(BaseModel):
    chrstn_mno: str = Field(..., description="충전소 관리번호")
    name: str = Field(..., description="충전소 이름")
    road_nm_addr: str | None = Field(default=None, description="도로명 주소")
    distance_km: float = Field(..., description="현재 위치에서 충전소까지의 거리 (km)")
    ntsl_pc: int | None = Field(default=None, description="수소 판매 가격 (원/kg)")
    price_diff_from_avg: float = Field(
        ..., description="반경 내 평균 대비 가격 차이 (음수면 평균보다 저렴)"
    )
    estimated_cost: int = Field(..., description="예상 충전 비용 (원)")
    wait_vhcle_alge: int | None = Field(default=None, description="대기 차량 대수")
    is_open: bool = Field(..., description="운영 여부 (oper_yn == 'Y')")
    let: float = Field(..., description="충전소 위도")
    lon: float = Field(..., description="충전소 경도")
    badge: str | None = Field(
        default=None, description="추천소 강조 칩 (예: '근처 최저가'/'대기 없음', 근거 없으면 null)"
    )
    realtime_price: bool = Field(
        default=False, description="단가가 실시간 갱신 데이터인지 (rltm_info_yn == 'Y')"
    )
    eta_minutes: int = Field(default=0, description="현재 위치→충전소 예상 소요 분 (근사)")
    available: bool = Field(
        default=True, description="지금 충전 가능 여부 (is_open and wait < 5)"
    )

    model_config = ConfigDict(from_attributes=True)


class NearestRecommendationResponse(BaseModel):
    screen: str = Field(..., description="화면 식별자 (battery_ + status)")
    vehicle: NearestRecommendationVehicleResponse = Field(..., description="차량 정보")
    ai_insight: NearestRecommendationInsight = Field(..., description="AI 인사이트")
    recommended_station: NearestRecommendationStation | None = Field(
        default=None, description="추천 충전소 (최저가 1곳, 없으면 null)"
    )

    model_config = ConfigDict(from_attributes=True)
