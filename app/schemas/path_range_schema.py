from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.hydrogen_station_schema import HydrogenStationResponse


class GeoBoundingBox(BaseModel):
    lat_min: float = Field(..., description="최소 위도")
    lat_max: float = Field(..., description="최대 위도")
    lng_min: float = Field(..., description="최소 경도")
    lng_max: float = Field(..., description="최대 경도")


class PathRangeStationSearchRequest(BaseModel):
    start_latitude: Decimal = Field(..., ge=-90, le=90, description="출발지 위도")
    start_longitude: Decimal = Field(..., ge=-180, le=180, description="출발지 경도")
    destination_latitude: Decimal = Field(..., ge=-90, le=90, description="목적지 위도")
    destination_longitude: Decimal = Field(
        ...,
        ge=-180,
        le=180,
        description="목적지 경도",
    )
    actual_distance_km: Decimal = Field(..., gt=0, description="실제 경로 거리")
    padding_km: Decimal = Field(
        default=Decimal("5.0"),
        ge=0,
        description="외접 범위 확장 및 내접 범위 축소 여유 거리",
    )


class PathRangeStationSearchResponse(BaseModel):
    circumscribed_box: GeoBoundingBox = Field(..., description="외접 검색 범위")
    inscribed_box: GeoBoundingBox = Field(..., description="제외할 내접 범위")
    top_box: GeoBoundingBox = Field(..., description="링 상단 검색 범위")
    bottom_box: GeoBoundingBox = Field(..., description="링 하단 검색 범위")
    left_box: GeoBoundingBox = Field(..., description="링 좌측 검색 범위")
    right_box: GeoBoundingBox = Field(..., description="링 우측 검색 범위")
    candidate_stations: list[HydrogenStationResponse] = Field(
        default_factory=list,
        description="경로 범위에 포함된 충전소 후보",
    )
