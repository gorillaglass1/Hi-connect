from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.hydrogen_charger_schema import HydrogenChargerCreate, HydrogenChargerResponse
from app.services.hydrogen_charger_service import HydrogenChargerService

router = APIRouter(prefix="/hydrogen-chargers", tags=["hydrogen-chargers"])


@router.post("", response_model=HydrogenChargerResponse, status_code=201)
async def create_charger(payload: HydrogenChargerCreate, db: AsyncSession = Depends(get_db)):
    return await HydrogenChargerService(db).create_charger(payload)


@router.get("", response_model=list[HydrogenChargerResponse])
async def list_chargers(
    hydrogen_charger_id: int | None = None,
    hydrogen_station_id: int | None = None,
    charger_status: str | None = None,
    pressure_type: str | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    return await HydrogenChargerService(db).get_chargers(
        hydrogen_charger_id,
        hydrogen_station_id,
        charger_status,
        pressure_type,
        limit,
        offset,
    )
