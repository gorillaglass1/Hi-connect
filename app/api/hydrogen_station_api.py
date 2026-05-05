from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.hydrogen_station_schema import (
    HydrogenStationCreate,
    HydrogenStationResponse,
    HydrogenStationUpdate,
)
from app.services.hydrogen_station_service import HydrogenStationService

router = APIRouter(prefix="/hydrogen-stations", tags=["hydrogen-stations"])


@router.post("", response_model=HydrogenStationResponse, status_code=201)
async def create_station(payload: HydrogenStationCreate, db: AsyncSession = Depends(get_db)):
    return await HydrogenStationService(db).create_station(payload)


@router.get("", response_model=list[HydrogenStationResponse])
async def list_stations(
    hydrogen_station_id: int | None = None,
    name: str | None = None,
    address: str | None = None,
    payment_supported: str | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    return await HydrogenStationService(db).get_stations(
        hydrogen_station_id,
        name,
        address,
        payment_supported,
        limit,
        offset,
    )

@router.patch("/{hydrogen_station_id}", response_model=HydrogenStationResponse)
async def update_station(
    hydrogen_station_id: int,
    payload: HydrogenStationUpdate,
    db: AsyncSession = Depends(get_db),
):
    return await HydrogenStationService(db).update_station(hydrogen_station_id, payload)
