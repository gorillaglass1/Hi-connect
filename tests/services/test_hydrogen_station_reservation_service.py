from datetime import datetime, timedelta

import pytest
from fastapi import HTTPException

from app.schemas.hydrogen_station_reservation_schemas import HydrogenStationReservationCreate
from app.services.hydrogen_station_reservation_service import HydrogenStationReservationService
from tests.test_data_factory import seed_base_entities


@pytest.mark.asyncio
async def test_create_reservation_invalid_time_raises_400(db_session):
    base = await seed_base_entities(db_session)
    service = HydrogenStationReservationService(db_session)
    now = datetime.now()

    with pytest.raises(HTTPException) as exc:
        await service.create_reservation(
            HydrogenStationReservationCreate(
                hydrogen_charger_id=base["charger"].hydrogen_charger_id,
                hydrogen_station_id=base["station"].hydrogen_station_id,
                reservation_status="RESERVED",
                user_id=base["user"].user_id,
                reservation_time=now,
                expire_time=now - timedelta(minutes=1),
            )
        )

    assert exc.value.status_code == 400
