import pytest
from fastapi import HTTPException

from app.schemas.hydrogen_station_schema import HydrogenStationCreate
from app.services.hydrogen_station_service import HydrogenStationService


@pytest.mark.asyncio
async def test_create_station_negative_total_chargers_raises_400(db_session):
    service = HydrogenStationService(db_session)
    with pytest.raises(HTTPException) as exc:
        await service.create_station(
            HydrogenStationCreate(
                name="A",
                address="B",
                latitude=37.5,
                longitude=127.0,
                total_chargers=-1,
            )
        )
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_get_station_by_id_not_found_raises_404(db_session):
    service = HydrogenStationService(db_session)
    with pytest.raises(HTTPException) as exc:
        await service.get_station_by_id(99999)
    assert exc.value.status_code == 404
