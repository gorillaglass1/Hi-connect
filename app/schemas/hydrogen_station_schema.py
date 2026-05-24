from datetime import datetime, time
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.hydrogen_station_facilities_schema import (
    HydrogenStationAdditionalInfoResponse,
)
from app.schemas.hydrogen_station_status_schema import HydrogenStationStatusResponse


class HydrogenStationCreate(BaseModel):
    chrstn_mno: str
    chrstn_nm: str
    chrstn_cttpc: str | None = Field(default=None)

    road_nm_addr: str | None = Field(default=None)
    lotno_addr: str | None = Field(default=None)

    cmpt_yn: str | None = Field(default=None)

    chrstn_ty_cd: str | None = Field(default=None)
    chrstn_ty_nm: str | None = Field(default=None)

    echrgeqp_ty_cd: str | None = Field(default=None)
    echrgeqp_ty_nm: str | None = Field(default=None)

    chrgr_ty_cd: str | None = Field(default=None)
    chrgr_ty_nm: str | None = Field(default=None)

    chrstn_ty_rm: str | None = Field(default=None)

    spldmd_mn_mthd_cd: str | None = Field(default=None)
    spldmd_mn_mthd_nm: str | None = Field(default=None)

    event_cn: str | None = Field(default=None)

    vhcle_knd_cd: str | None = Field(default=None)
    vhcle_knd_nm: str | None = Field(default=None)

    ntsl_pc: int | None = Field(default=None)

    setle_mthd_cd: str | None = Field(default=None)
    setle_mthd_nm: str | None = Field(default=None)

    use_posbl_dotw: str | None = Field(default=None)

    usebhr_hr_mon: time | None = Field(default=None)
    useehr_hr_mon: time | None = Field(default=None)

    usebhr_hr_tues: time | None = Field(default=None)
    useehr_hr_tues: time | None = Field(default=None)

    usebhr_hr_wed: time | None = Field(default=None)
    useehr_hr_wed: time | None = Field(default=None)

    usebhr_hr_thur: time | None = Field(default=None)
    useehr_hr_thur: time | None = Field(default=None)

    usebhr_hr_fri: time | None = Field(default=None)
    useehr_hr_fri: time | None = Field(default=None)

    usebhr_hr_sat: time | None = Field(default=None)
    useehr_hr_sat: time | None = Field(default=None)

    usebhr_hr_sun: time | None = Field(default=None)
    useehr_hr_sun: time | None = Field(default=None)

    usebhr_hr_hldy: time | None = Field(default=None)
    useehr_hr_hldy: time | None = Field(default=None)

    rest_bgng_hr: time | None = Field(default=None)
    rest_end_hr: time | None = Field(default=None)

    rsvt_posbl_yn: str | None = Field(default=None)

    lon: Decimal | None = Field(default=None)
    let: Decimal | None = Field(default=None)

    oper_yn: str | None = Field(default=None)
    del_at: str | None = Field(default="0")

    last_mdfcn_dt: datetime | None = Field(default=None)
    timestamp: datetime | None = Field(default=None)

    rltm_info_yn: str | None = Field(default=None)

    @field_validator(
        "usebhr_hr_mon",
        "useehr_hr_mon",
        "usebhr_hr_tues",
        "useehr_hr_tues",
        "usebhr_hr_wed",
        "useehr_hr_wed",
        "usebhr_hr_thur",
        "useehr_hr_thur",
        "usebhr_hr_fri",
        "useehr_hr_fri",
        "usebhr_hr_sat",
        "useehr_hr_sat",
        "usebhr_hr_sun",
        "useehr_hr_sun",
        "usebhr_hr_hldy",
        "useehr_hr_hldy",
        "rest_bgng_hr",
        "rest_end_hr",
        mode="before",
    )
    @classmethod
    def parse_time(cls, value):
        if value is None or value == "":
            return None
        if isinstance(value, time):
            return value
        if value == "24:00":
            return time(23, 59, 59)
        return value

    @field_validator("last_mdfcn_dt", mode="before")
    @classmethod
    def parse_last_mdfcn_dt(cls, value):
        if value is None or value == "":
            return None

        if isinstance(value, datetime):
            return value

        return datetime.strptime(value, "%Y%m%d%H%M%S")

    @field_validator("timestamp", mode="before")
    @classmethod
    def parse_timestamp(cls, value):
        if value is None or value == "":
            return None

        if isinstance(value, datetime):
            return value

        # 예: "2024-03-07 15:08:00:452993 +09:00"
        if isinstance(value, str):
            value = value.split(" +")[0]

            if value.count(":") == 3:
                base_time, microsecond = value.rsplit(":", 1)
                value = f"{base_time}.{microsecond}"

            return datetime.strptime(value, "%Y-%m-%d %H:%M:%S.%f")

        return value


class HydrogenStationResponse(HydrogenStationCreate):
    model_config = ConfigDict(from_attributes=True)


class HydrogenStationDetailResponse(HydrogenStationResponse):
    status: HydrogenStationStatusResponse | None = Field(default=None)
    facilities: list[HydrogenStationAdditionalInfoResponse] = Field(default_factory=list)
