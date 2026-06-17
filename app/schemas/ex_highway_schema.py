from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class RestAreaWeatherItem(BaseModel):
    """한국도로공사 휴게소별 날씨 정보 단일 항목.

    외부 API의 camelCase 응답을 snake_case로 매핑한다.
    """

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    sdate: str | None = Field(default=None, description="날짜")
    std_hour: str | None = Field(default=None, validation_alias="stdHour", description="시간대")
    unit_code: str | None = Field(default=None, validation_alias="unitCode", description="휴게소코드")
    unit_name: str | None = Field(default=None, validation_alias="unitName", description="휴게소명")
    route_no: str | None = Field(default=None, validation_alias="routeNo", description="노선번호")
    route_name: str | None = Field(default=None, validation_alias="routeName", description="도로명")
    updown_type_code: str | None = Field(
        default=None, validation_alias="updownTypeCode", description="방향(S:기점/E:종점)"
    )
    x_value: str | None = Field(default=None, validation_alias="xValue", description="X좌표값")
    y_value: str | None = Field(default=None, validation_alias="yValue", description="Y좌표값")
    tmx_value: str | None = Field(default=None, validation_alias="tmxValue", description="TM_X좌표값")
    tmy_value: str | None = Field(default=None, validation_alias="tmyValue", description="TM_Y좌표값")
    measurement: str | None = Field(default=None, description="측정소명")
    addr: str | None = Field(default=None, description="주소")
    addr_code: str | None = Field(default=None, validation_alias="addrCode", description="기상실황지역코드")
    addr_name: str | None = Field(default=None, validation_alias="addrName", description="기상실황지역명")
    weather_contents: str | None = Field(
        default=None, validation_alias="weatherContents", description="현재일기내용"
    )
    status_no: str | None = Field(default=None, validation_alias="statusNo", description="현상번호값")
    correct_no: str | None = Field(default=None, validation_alias="correctNo", description="시정값")
    cloud_value: str | None = Field(default=None, validation_alias="cloudValue", description="전운량값")
    addcloud_value: str | None = Field(
        default=None, validation_alias="addcloudValue", description="증하운량값"
    )
    cloudform_value: str | None = Field(
        default=None, validation_alias="cloudformValue", description="운형값"
    )
    temp_value: str | None = Field(default=None, validation_alias="tempValue", description="현재기온값")
    dew_value: str | None = Field(default=None, validation_alias="dewValue", description="이슬점온도")
    discomfore_value: str | None = Field(
        default=None, validation_alias="discomforeValue", description="불쾌지수값"
    )
    sensory_temp: str | None = Field(default=None, validation_alias="sensoryTemp", description="체감온도")
    highest_temp: str | None = Field(default=None, validation_alias="highestTemp", description="최고온도")
    highestyear_temp: str | None = Field(
        default=None, validation_alias="highestyearTemp", description="평년최고기온값"
    )
    highestcomp_temp: str | None = Field(
        default=None, validation_alias="highestcompTemp", description="평비최고기온값"
    )
    lowest_temp: str | None = Field(default=None, validation_alias="lowestTemp", description="최저기온값")
    lowestyear_temp: str | None = Field(
        default=None, validation_alias="lowestyearTemp", description="평년최저기온값"
    )
    lowestcomp_temp: str | None = Field(
        default=None, validation_alias="lowestcompTemp", description="평비최저기온값"
    )
    rainfall_value: str | None = Field(
        default=None, validation_alias="rainfallValue", description="일강수값"
    )
    rainfallstrength_value: str | None = Field(
        default=None, validation_alias="rainfallstrengthValue", description="강수강도값"
    )
    newsnow_value: str | None = Field(
        default=None, validation_alias="newsnowValue", description="신적설량값"
    )
    snow_value: str | None = Field(default=None, validation_alias="snowValue", description="적설량값")
    humidity_value: str | None = Field(
        default=None, validation_alias="humidityValue", description="상대습도값"
    )
    wind_contents: str | None = Field(
        default=None, validation_alias="windContents", description="풍향내용"
    )
    wind_value: str | None = Field(default=None, validation_alias="windValue", description="풍속값")


class RestAreaWeatherResponse(BaseModel):
    """휴게소별 날씨 정보 응답."""

    code: str | None = Field(default=None, description="결과 코드")
    message: str | None = Field(default=None, description="결과 메시지")
    count: int | None = Field(default=None, description="전체 결과 수")
    items: list[RestAreaWeatherItem] = Field(default_factory=list, description="휴게소 날씨 목록")


class RealtimeTrafficItem(BaseModel):
    """한국도로공사 실시간 교통량 단일 항목."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    std_date: str | None = Field(default=None, validation_alias="stdDate", description="수집일자")
    std_hour: str | None = Field(default=None, validation_alias="stdHour", description="수집시각")
    vds_id: str | None = Field(default=None, validation_alias="vdsId", description="VDS_ID")
    traffic_amount: str | None = Field(
        default=None,
        validation_alias=AliasChoices("trafficAmout", "trafficAmount"),
        description="교통량(대)",
    )
    speed: str | None = Field(default=None, description="속도(km/h)")
    share_ratio: str | None = Field(default=None, validation_alias="shareRatio", description="점유율")
    time_avg: str | None = Field(default=None, validation_alias="timeAvg", description="통행시간")
    grade: str | None = Field(
        default=None,
        description="소통등급 [0:판정불가][1:소통원활(80km↑)][2:서행(40~80km)][3:정체(0~40km)]",
    )
    route_no: str | None = Field(default=None, validation_alias="routeNo", description="노선번호")
    route_name: str | None = Field(default=None, validation_alias="routeName", description="도로명")
    updown_type_code: str | None = Field(
        default=None, validation_alias="updownTypeCode", description="방향(S:기점/E:종점)"
    )
    conzone_id: str | None = Field(default=None, validation_alias="conzoneId", description="콘존ID")
    conzone_name: str | None = Field(
        default=None, validation_alias="conzoneName", description="콘존명"
    )


class RealtimeTrafficResponse(BaseModel):
    """실시간 교통량 응답."""

    code: str | None = Field(default=None, description="결과 코드")
    message: str | None = Field(default=None, description="결과 메시지")
    count: int | None = Field(default=None, description="전체 결과 수")
    items: list[RealtimeTrafficItem] = Field(default_factory=list, description="실시간 교통량 목록")
