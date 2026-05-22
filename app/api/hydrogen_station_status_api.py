from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.hydrogen_station_status_schemas import (
    HydrogenStationStatusCreate,
    HydrogenStationStatusResponse,
)
from app.services.hydrogen_station_status_service import HydrogenStationStatusService

router = APIRouter(
    prefix="/hydrogen-station-status",
    tags=["hydrogen-station-status"],
)


@router.post("", response_model=HydrogenStationStatusResponse, status_code=201)
async def create_hydrogen_station_status(
    payload: HydrogenStationStatusCreate,
    db: AsyncSession = Depends(get_db),
):
    return await HydrogenStationStatusService(db).create_hydrogen_station_status(payload)


@router.get("", response_model=list[HydrogenStationStatusResponse])
async def list_hydrogen_station_statuses(
    chrstn_mno: str | None = None,
    oper_sttus_cd: str | None = None,
    pos_sttus_cd: str | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    return await HydrogenStationStatusService(db).get_hydrogen_station_statuses(
        chrstn_mno=chrstn_mno,
        oper_sttus_cd=oper_sttus_cd,
        pos_sttus_cd=pos_sttus_cd,
        limit=limit,
        offset=offset,
    )


@router.post("/sync")
async def sync_hydrogen_station_statuses(
    page_no: int | None = Query(default=None, ge=1),
    num_of_rows: int | None = Query(default=None, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    params = {}
    if page_no is not None:
        params["pageNo"] = page_no
    if num_of_rows is not None:
        params["numOfRows"] = num_of_rows
    return await HydrogenStationStatusService(db).sync_from_hying(params or None)
