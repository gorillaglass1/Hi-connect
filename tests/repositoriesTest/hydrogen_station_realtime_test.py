import pytest
import pytest_asyncio
from sqlalchemy import Column, Integer
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base
from app.models.hydrogen_station_realtime import HydrogenStationRealtime  # noqa: F401
from app.repositories.hydrogen_station_realtime_repo import (
    get_station_realtime,
    upsert_station_realtime,
)


class HydrogenStation(Base):
    __tablename__ = "hydrogen_station"
    __table_args__ = {"extend_existing": True}
    hydrogen_station_id = Column(Integer, primary_key=True)


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
async def test_upsert_station_realtime(db_session: AsyncSession):
    first = await upsert_station_realtime(
        db_session,
        hydrogen_station_id=1,
        queue_count=3,
        avg_wait_time=10,
        station_status="BUSY",
    )
    second = await upsert_station_realtime(
        db_session,
        hydrogen_station_id=1,
        queue_count=1,
        avg_wait_time=4,
        station_status="AVAILABLE",
    )

    rows = await get_station_realtime(db_session, hydrogen_station_id=1, limit=1)
    row = rows[0]

    assert first.realtime_id == second.realtime_id
    assert row.queue_count == 1
    assert row.station_status == "AVAILABLE"
