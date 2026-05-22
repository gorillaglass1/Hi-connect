from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.hydrogen_station_facilities import (
    HydrogenStationAdditionalInfoCreate,
    HydrogenStationAdditionalInfoResponse,
)
from app.services.hydrogen_station_facilities_service import (
    HydrogenStationFacilitiesService,
)

router = APIRouter(
    prefix="/hydrogen-station-facilities",
    tags=["hydrogen-station-facilities"],
)


@router.post("", response_model=HydrogenStationAdditionalInfoResponse, status_code=201)
async def create_hydrogen_station_facility(
    payload: HydrogenStationAdditionalInfoCreate,
    db: AsyncSession = Depends(get_db),
):
    return await HydrogenStationFacilitiesService(db).create_hydrogen_station_facility(
        payload
    )


@router.get("", response_model=list[HydrogenStationAdditionalInfoResponse])
async def list_hydrogen_station_facilities(
    chrstn_mno: str | None = None,
    adi_info_se_cd: str | None = None,
    del_at: str | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    return await HydrogenStationFacilitiesService(db).get_hydrogen_station_facilities(
        chrstn_mno=chrstn_mno,
        adi_info_se_cd=adi_info_se_cd,
        del_at=del_at,
        limit=limit,
        offset=offset,
    )


@router.post("/sync")
async def sync_hydrogen_station_facilities(
    db: AsyncSession = Depends(get_db),
):
    return await HydrogenStationFacilitiesService(db).sync_from_hying()
