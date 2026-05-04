from datetime import datetime, timedelta

import pytest
from fastapi import HTTPException

from app.schemas.charging_log_schemas import ChargingLogCreate
from app.services.charging_log_service import ChargingLogService
from tests.test_data_factory import seed_base_entities


@pytest.mark.asyncio
async def test_create_charging_log_invalid_time_raises_400(db_session):
    base = await seed_base_entities(db_session)
    service = ChargingLogService(db_session)
    now = datetime.now()

    with pytest.raises(HTTPException) as exc:
        await service.create_charging_log(
            ChargingLogCreate(
                user_id=base["user"].user_id,
                hydrogen_station_id=base["station"].hydrogen_station_id,
                vehicle_id=base["vehicle"].vehicle_id,
                start_time=now,
                end_time=now - timedelta(minutes=1),
            )
        )

    assert exc.value.status_code == 400
