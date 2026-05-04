import pytest
from fastapi import HTTPException

from app.schemas.hydrogen_charger_schema import HydrogenChargerCreate
from app.services.hydrogen_charger_service import HydrogenChargerService
from tests.test_data_factory import seed_base_entities


@pytest.mark.asyncio
async def test_create_charger_negative_pressure_raises_400(db_session):
    base = await seed_base_entities(db_session)
    service = HydrogenChargerService(db_session)

    with pytest.raises(HTTPException) as exc:
        await service.create_charger(
            HydrogenChargerCreate(
                hydrogen_station_id=base["station"].hydrogen_station_id,
                charger_status="충분",
                pressure_type="700bar",
                hydrogen_pressure_bar=-100,
            )
        )
    assert exc.value.status_code == 400
