import pytest

from app.repositories.vehicles_repo import create_vehicle, get_vehicles
from tests.test_data_factory import seed_base_entities


@pytest.mark.asyncio
async def test_get_vehicles_filter_by_vehicle_number(db_session):
    base = await seed_base_entities(db_session)
    rows = await get_vehicles(db_session, vehicle_number=base["vehicle"].vehicle_number)
    assert len(rows) == 1


@pytest.mark.asyncio
async def test_create_vehicle_success(db_session):
    base = await seed_base_entities(db_session)
    row = await create_vehicle(
        db_session,
        user_id=base["user"].user_id,
        vehicle_number="34가5678",
        model="NEXO2",
        vehicle_type="SUV",
        tank_capacity=6.5,
    )
    assert row.vehicle_id is not None
