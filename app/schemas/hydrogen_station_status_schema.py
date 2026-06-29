from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class HydrogenStationStatusCreate(BaseModel):
    chrstn_mno: str

    tt_pressr: int | None = Field(default=None)
    prfect_elctc_posbl_alge: int | None = Field(default=None)
    wait_vhcle_alge: int | None = Field(default=None)

    cnf_sttus_cd: str | None = Field(default=None)
    cnf_sttus_nm: str | None = Field(default=None)

    oper_sttus_cd: str | None = Field(default=None)
    oper_sttus_nm: str | None = Field(default=None)

    pos_sttus_cd: str | None = Field(default=None)
    pos_sttus_nm: str | None = Field(default=None)

    last_mdfcn_dt: datetime | None = Field(default=None)

    @field_validator("last_mdfcn_dt", mode="before")
    @classmethod
    def parse_last_mdfcn_dt(cls, value):
        if value is None or value == "":
            return None

        if isinstance(value, datetime):
            return value

        return datetime.strptime(value, "%Y%m%d%H%M%S")


class HydrogenStationStatusResponse(HydrogenStationStatusCreate):
    status_id: int
    created_at: datetime | None = Field(default=None)
    updated_at: datetime | None = Field(default=None)

    model_config = ConfigDict(from_attributes=True)