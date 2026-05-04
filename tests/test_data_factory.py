from datetime import datetime, timedelta, time
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.charging_log_repo import create_charging_log
from app.repositories.hydrogen_charger_repo import create_hydrogen_charger
from app.repositories.hydrogen_station_repo import create_hydrogen_station
from app.repositories.hydrogen_station_reservation_repo import create_reservation
from app.repositories.recommendation_history_repo import create_recommendation_history
from app.repositories.user_repo import create_user
from app.repositories.vehicles_repo import create_vehicle


async def seed_base_entities(db_session: AsyncSession):
    suffix = uuid.uuid4().hex[:8]
    user = await create_user(
        db_session,
        name="Tester",
        email=f"seed-{suffix}@example.com",
        phone="010-0000-0000",
    )
    station = await create_hydrogen_station(
        db_session,
        name=f"Seed Station {suffix}",
        address="Seoul",
        latitude=37.5,
        longitude=127.0,
        contact_number="02-111-2222",
        start_time=time(8, 0),
        end_time=time(20, 0),
        total_chargers=3,
        payment_supported="CARD",
    )
    vehicle = await create_vehicle(
        db_session,
        user_id=user.user_id,
        vehicle_number=f"{suffix[:2]}가{suffix[2:6]}",
        model="NEXO",
        vehicle_type="SUV",
        fuel_type="hydrogen",
        tank_capacity=6.3,
        avg_efficiency=100.0,
    )
    charger = await create_hydrogen_charger(
        db_session,
        hydrogen_station_id=station.hydrogen_station_id,
        charger_status="충분",
        pressure_type="700bar",
        charger_type="FAST",
        hydrogen_pressure_bar=700,
    )

    return {
        "user": user,
        "station": station,
        "vehicle": vehicle,
        "charger": charger,
    }


async def seed_all_entities(db_session: AsyncSession):
    base = await seed_base_entities(db_session)
    now = datetime.now()

    charging_log = await create_charging_log(
        db_session,
        user_id=base["user"].user_id,
        hydrogen_station_id=base["station"].hydrogen_station_id,
        vehicle_id=base["vehicle"].vehicle_id,
        start_time=now,
        end_time=now + timedelta(minutes=20),
        charged_amount=3.1,
        charging_cost=21000,
        waiting_time=3,
    )

    reservation = await create_reservation(
        db_session,
        hydrogen_charger_id=base["charger"].hydrogen_charger_id,
        hydrogen_station_id=base["station"].hydrogen_station_id,
        user_id=base["user"].user_id,
        reservation_time=now + timedelta(minutes=10),
        expire_time=now + timedelta(minutes=30),
    )

    recommendation = await create_recommendation_history(
        db_session,
        user_id=base["user"].user_id,
        vehicle_id=base["vehicle"].vehicle_id,
        hydrogen_station_id=base["station"].hydrogen_station_id,
        recommendation_score=95.5,
        recommendation_reason="closest",
        selected=True,
        recommendation_type="distance",
    )

    return {
        **base,
        "charging_log": charging_log,
        "reservation": reservation,
        "recommendation": recommendation,
    }
