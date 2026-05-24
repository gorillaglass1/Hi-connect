from decimal import Decimal
from pydantic import BaseModel, Field


class RecommendationSearchRequest(BaseModel):
    user_id: int = Field(..., description="사용자 ID")
    current_latitude: Decimal = Field(..., description="현재 위치 위도")
    current_longitude: Decimal = Field(..., description="현재 위치 경도")
    destination_latitude: Decimal = Field(..., description="목적지 위치 위도")
    destination_longitude: Decimal = Field(..., description="목적지 위치 경도")
    remaining_range: Decimal = Field(..., description="현재 차량 주행가능거리 (km)")
    alpha: Decimal = Field(default=Decimal("15.0"), description="직선 거리 대비 검색 반경 버퍼 (km)")
    nl_query: str | None = Field(default=None, description="자연어 필터 검색 조건 (Text-to-SQL)")


class SubScores(BaseModel):
    price: float = Field(..., description="가격 부문 점수 (0-100)")
    waiting_time: float = Field(..., description="대기시간 부문 점수 (0-100)")
    distance: float = Field(..., description="우회거리 부문 점수 (0-100)")
    facilities: float = Field(..., description="부대시설 부문 점수 (0-100)")


class RecommendationDeliveryPayload(BaseModel):
    chrstn_mno: str = Field(..., description="충전소 관리번호")
    chrstn_nm: str = Field(..., description="충전소 이름")
    road_nm_addr: str | None = Field(None, description="도로명 주소")
    latitude: float = Field(..., description="충전소 위도")
    longitude: float = Field(..., description="충전소 경도")
    ntsl_pc: int | None = Field(None, description="수소 가격 (원/kg)")
    distance_to_station: float = Field(..., description="현재 위치에서 충전소까지의 거리 (km)")
    detour_distance: float = Field(..., description="우회 거리 (km)")
    wait_vehicles: int = Field(..., description="대기 차량 수")
    wait_time_minutes: int = Field(..., description="예상 대기 시간 (분)")
    facilities: list[str] = Field(..., description="제공 편의시설 리스트")
    is_reachable: bool = Field(..., description="현재 주행가능거리 내 도달 가능 여부")
    final_score: float = Field(..., description="최종 추천 점수")
    recommendation_reason: str = Field(..., description="추천 사유")


class RecommendedStationResponse(BaseModel):
    chrstn_mno: str = Field(..., description="충전소 관리번호")
    chrstn_nm: str = Field(..., description="충전소 이름")
    road_nm_addr: str | None = Field(None, description="도로명 주소")
    ntsl_pc: int | None = Field(None, description="수소 가격 (원/kg)")
    distance_to_station: float = Field(..., description="현재 위치에서 충전소까지의 거리 (km)")
    distance_to_destination: float = Field(..., description="충전소에서 목적지까지의 거리 (km)")
    detour_distance: float = Field(..., description="우회 거리 (km)")
    wait_vehicles: int = Field(..., description="대기 차량 수")
    wait_time_minutes: int = Field(..., description="예상 대기 시간 (분)")
    facilities: list[str] = Field(..., description="제공 편의시설 리스트")
    is_reachable: bool = Field(..., description="현재 주행가능거리 내 도달 가능 여부")
    sub_scores: SubScores = Field(..., description="세부 항목 점수")
    final_score: float = Field(..., description="최종 추천 점수 (0-100)")
    recommendation_reason: str = Field(..., description="개인화 추천 사유 요약")
    delivery_payload: RecommendationDeliveryPayload = Field(
        ...,
        description="외부 시스템에 전달 가능한 표준 추천 JSON payload",
    )
