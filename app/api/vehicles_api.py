from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.vehicles_schema import VehicleCreate, VehicleResponse
from app.services.vehicle_service import VehicleService

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router.post("", response_model=VehicleResponse, status_code=201)
async def create_vehicle(payload: VehicleCreate, db: AsyncSession = Depends(get_db)):
    return await VehicleService(db).create_vehicle(payload)


@router.get("", response_model=list[VehicleResponse])
async def list_vehicles(
    vehicle_id: int | None = None,
    user_id: int | None = None,
    vehicle_number: str | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    return await VehicleService(db).get_vehicles(vehicle_id, user_id, vehicle_number, limit, offset)


@router.get("/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle(vehicle_id: int, db: AsyncSession = Depends(get_db)):
    return await VehicleService(db).get_vehicle_by_id(vehicle_id)
