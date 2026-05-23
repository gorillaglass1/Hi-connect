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


class GeoPoint(BaseModel):
    latitude: float = Field(..., description="위도")
    longitude: float = Field(..., description="경도")


class DeliveryStation(BaseModel):
    chrstn_mno: str = Field(..., description="충전소 관리번호")
    name: str = Field(..., description="충전소명")
    address: str | None = Field(default=None, description="충전소 주소")
    location: GeoPoint = Field(..., description="충전소 위치")


class DeliveryRouteContext(BaseModel):
    current_location: GeoPoint = Field(..., description="현재 위치")
    destination: GeoPoint = Field(..., description="목적지 위치")
    remaining_range_km: float = Field(..., description="현재 차량 주행가능거리")
    distance_to_station_km: float = Field(..., description="현재 위치에서 충전소까지 거리")
    distance_to_destination_km: float = Field(..., description="충전소에서 목적지까지 거리")
    detour_distance_km: float = Field(..., description="우회 거리")
    is_reachable: bool = Field(..., description="현재 주행가능거리 내 도달 가능 여부")


class RecommendationDeliveryPayload(BaseModel):
    schema_version: str = Field(default="1.0", description="전송 payload 스키마 버전")
    source: str = Field(default="HY_CONNECT", description="payload 생성 주체")
    user_id: int = Field(..., description="사용자 ID")
    recommendation_type: str = Field(..., description="추천 타입")
    station: DeliveryStation = Field(..., description="추천 충전소")
    route_context: DeliveryRouteContext = Field(..., description="경로 및 차량 컨텍스트")
    scores: SubScores = Field(..., description="세부 점수")
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
    hyundai_nav_deeplink: str = Field(..., description="데모용 내비 경유지 딥링크")
