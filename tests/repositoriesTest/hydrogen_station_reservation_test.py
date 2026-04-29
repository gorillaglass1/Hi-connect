from datetime import datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy import Column, Integer
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base
from app.models.hydrogen_station_reservation import HydrogenStationReservation  # noqa: F401
from app.models.user import User  # noqa: F401
from app.repositories.hydrogen_station_reservation_repo import (
    create_reservation,
    get_reservations,
)


class HydrogenStation(Base):
    __tablename__ = "hydrogen_station"
    __table_args__ = {"extend_existing": True}
    hydrogen_station_id = Column(Integer, primary_key=True)


class HydrogenCharger(Base):
    __tablename__ = "hydrogen_charger"
    __table_args__ = {"extend_existing": True}
    hydrogen_charger_id = Column(Integer, primary_key=True)


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session():
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.mark.asyncio
async def test_get_active_reservations_by_station(db_session: AsyncSession):
    now = datetime.now()
    await create_reservation(
        db_session,
        hydrogen_charger_id=1,
        hydrogen_station_id=1,
        user_id=1,
        reservation_time=now,
        expire_time=now + timedelta(minutes=30),
    )

    rows = await get_reservations(
        db_session,
        hydrogen_station_id=1,
        reservation_status="RESERVED",
    )

    assert len(rows) == 1
    assert rows[0].reservation_status == "RESERVED"
