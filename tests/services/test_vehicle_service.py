import pytest
from fastapi import HTTPException

from app.schemas.vehicles_schema import VehicleCreate
from app.services.vehicle_service import VehicleService
from tests.test_data_factory import seed_base_entities


@pytest.mark.asyncio
async def test_create_vehicle_duplicate_number_raises_409(db_session):
    base = await seed_base_entities(db_session)
    service = VehicleService(db_session)

    with pytest.raises(HTTPException) as exc:
        await service.create_vehicle(
            VehicleCreate(
                user_id=base["user"].user_id,
                vehicle_number=base["vehicle"].vehicle_number,
                model="NEXO",
                vehicle_type="SUV",
                fuel_type="hydrogen",
                tank_capacity=6.3,
            )
        )

    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_get_vehicle_by_id_not_found_raises_404(db_session):
    service = VehicleService(db_session)
    with pytest.raises(HTTPException) as exc:
        await service.get_vehicle_by_id(999999)
    assert exc.value.status_code == 404
