from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import hydrogen_station_repo
from app.schemas.hydrogen_station_schema import (
    HydrogenStationCreate,
    HydrogenStationDetailResponse,
    HydrogenStationResponse,
)
from app.services.hying_client import HyingClient


class HydrogenStationService:
    def __init__(self, db: AsyncSession, hying_client: HyingClient | None = None):
        self.db = db
        self.hying_client = hying_client or HyingClient()

    async def create_hydrogen_station(self, payload: HydrogenStationCreate):
        existing = await hydrogen_station_repo.get_hydrogen_station_by_id(
            self.db, payload.chrstn_mno
        )
        if existing is not None:
            raise HTTPException(status_code=409, detail="Hydrogen station already exists")

        try:
            return await hydrogen_station_repo.create_hydrogen_station(self.db, payload)
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(status_code=409, detail="Hydrogen station already exists")

    async def get_hydrogen_stations(
        self,
        chrstn_mno: str | None = None,
        chrstn_nm: str | None = None,
        oper_yn: str | None = None,
        rltm_info_yn: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ):
        return await hydrogen_station_repo.get_hydrogen_stations(
            self.db,
            chrstn_mno=chrstn_mno,
            chrstn_nm=chrstn_nm,
            oper_yn=oper_yn,
            rltm_info_yn=rltm_info_yn,
            limit=limit,
            offset=offset,
        )

    async def get_hydrogen_station_detail(self, chrstn_mno: str):
        station = await hydrogen_station_repo.get_hydrogen_station_detail_by_id(
            self.db,
            chrstn_mno,
        )
        if station is None:
            raise HTTPException(status_code=404, detail="Hydrogen station not found")

        return self._to_detail_response(station)

    async def get_hydrogen_station_details(
        self,
        chrstn_mno: str | None = None,
        chrstn_nm: str | None = None,
        address: str | None = None,
        oper_yn: str | None = None,
        rltm_info_yn: str | None = None,
        rsvt_posbl_yn: str | None = None,
        oper_sttus_nm: str | None = None,
        pos_sttus_nm: str | None = None,
        cnf_sttus_nm: str | None = None,
        facility_nm: str | None = None,
        sort_by: str | None = None,
        sort_order: str = "asc",
        limit: int = 100,
        offset: int = 0,
    ):
        stations = await hydrogen_station_repo.get_hydrogen_station_details(
            self.db,
            chrstn_mno=chrstn_mno,
            chrstn_nm=chrstn_nm,
            address=address,
            oper_yn=oper_yn,
            rltm_info_yn=rltm_info_yn,
            rsvt_posbl_yn=rsvt_posbl_yn,
            oper_sttus_nm=oper_sttus_nm,
            pos_sttus_nm=pos_sttus_nm,
            cnf_sttus_nm=cnf_sttus_nm,
            facility_nm=facility_nm,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset,
        )
        return [self._to_detail_response(station) for station in stations]

    def _to_detail_response(self, station):
        station_data = HydrogenStationResponse.model_validate(station).model_dump()
        return HydrogenStationDetailResponse(
            **station_data,
            status=station.status_list[0] if station.status_list else None,
            facilities=station.facilities_list,
        )

    async def sync_from_hying(self, params: dict | None = None):
        items = await self.hying_client.fetch_stations(params)
        payloads = [HydrogenStationCreate.model_validate(item) for item in items]
        rows = await hydrogen_station_repo.upsert_hydrogen_stations(self.db, payloads)
        return {"fetched": len(items), "saved": len(rows)}
