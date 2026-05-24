from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.hydrogen_station_schema import (
    HydrogenStationCreate,
    HydrogenStationDetailResponse,
    HydrogenStationResponse,
)
from app.services.hydrogen_station_service import HydrogenStationService

router = APIRouter(prefix="/hydrogen-stations", tags=["hydrogen-stations"])


@router.post("", response_model=HydrogenStationResponse, status_code=201)
async def create_hydrogen_station(
    payload: HydrogenStationCreate,
    db: AsyncSession = Depends(get_db),
):
    return await HydrogenStationService(db).create_hydrogen_station(payload)


@router.get("", response_model=list[HydrogenStationResponse])
async def list_hydrogen_stations(
    chrstn_mno: str | None = None,
    chrstn_nm: str | None = None,
    oper_yn: str | None = None,
    rltm_info_yn: str | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    return await HydrogenStationService(db).get_hydrogen_stations(
        chrstn_mno=chrstn_mno,
        chrstn_nm=chrstn_nm,
        oper_yn=oper_yn,
        rltm_info_yn=rltm_info_yn,
        limit=limit,
        offset=offset,
    )


@router.get("/details", response_model=list[HydrogenStationDetailResponse])
async def list_hydrogen_station_details(
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
    sort_by: Literal[
        "chrstn_nm",
        "wait_vhcle_alge",
        "prfect_elctc_posbl_alge",
        "tt_pressr",
    ] = "chrstn_nm",
    sort_order: Literal["asc", "desc"] = "asc",
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    return await HydrogenStationService(db).get_hydrogen_station_details(
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


@router.get("/{chrstn_mno}", response_model=HydrogenStationDetailResponse)
async def get_hydrogen_station_detail(
    chrstn_mno: str,
    db: AsyncSession = Depends(get_db),
):
    return await HydrogenStationService(db).get_hydrogen_station_detail(chrstn_mno)


@router.post("/sync")
async def sync_hydrogen_stations(
    page_no: int | None = Query(default=None, ge=1),
    num_of_rows: int | None = Query(default=None, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    params = {}
    if page_no is not None:
        params["pageNo"] = page_no
    if num_of_rows is not None:
        params["numOfRows"] = num_of_rows
    return await HydrogenStationService(db).sync_from_hying(params or None)
