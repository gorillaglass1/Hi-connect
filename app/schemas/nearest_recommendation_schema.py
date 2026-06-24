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


class NearestRecommendationRequest(BaseModel):
    vehicle: NearestRecommendationVehicle = Field(..., description="차량 정보")
    location: NearestRecommendationLocation = Field(..., description="현재 위치")
    context: NearestRecommendationContext | None = Field(
        default=None, description="검색 컨텍스트 (선택)"
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

    model_config = ConfigDict(from_attributes=True)


class NearestRecommendationResponse(BaseModel):
    screen: str = Field(..., description="화면 식별자 (battery_ + status)")
    vehicle: NearestRecommendationVehicleResponse = Field(..., description="차량 정보")
    ai_insight: NearestRecommendationInsight = Field(..., description="AI 인사이트")
    recommended_station: NearestRecommendationStation | None = Field(
        default=None, description="추천 충전소 (최저가 1곳, 없으면 null)"
    )

    model_config = ConfigDict(from_attributes=True)
