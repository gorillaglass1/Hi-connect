from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class HydrogenStationAdditionalInfoCreate(BaseModel):
    chrstn_mno: str

    adi_info_se_cd: str | None = Field(default=None)
    adi_info_se_nm: str | None = Field(default=None)

    del_at: str | None = Field(default="0")

    last_mdfcn_dt: datetime | None = Field(default=None)
    timestamp: datetime | None = Field(default=None)

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

        if isinstance(value, str):
            # 예: "2022-01-19 01:32:24.340447 +00:00"
            # 예: "2026-05-22 15:45:14:205554 +09:00"
            value = value.split(" +")[0]
            if value.count(":") == 3:
                base_time, microsecond = value.rsplit(":", 1)
                value = f"{base_time}.{microsecond}"
            return datetime.strptime(value, "%Y-%m-%d %H:%M:%S.%f")

        return value


class HydrogenStationAdditionalInfoResponse(HydrogenStationAdditionalInfoCreate):
    additional_info_id: int
    created_at: datetime | None = Field(default=None)
    updated_at: datetime | None = Field(default=None)

    model_config = ConfigDict(from_attributes=True)

class HydrogenStationAdditionalInfoWithStationResponse(
    HydrogenStationAdditionalInfoResponse
):
    chrstn_nm: str | None = Field(default=None)
    road_nm_addr: str | None = Field(default=None)
