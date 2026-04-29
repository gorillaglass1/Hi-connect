import pytest
import pytest_asyncio
from sqlalchemy import Column, Integer
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base
from app.models.recommendation_history import RecommendationHistory  # noqa: F401
from app.models.user import User  # noqa: F401
from app.repositories.recommendation_history_repo import (
    create_recommendation_history,
    get_recommendations,
)


class HydrogenStation(Base):
    __tablename__ = "hydrogen_station"
    __table_args__ = {"extend_existing": True}
    hydrogen_station_id = Column(Integer, primary_key=True)


class Vehicle(Base):
    __tablename__ = "vehicles"
    __table_args__ = {"extend_existing": True}
    vehicle_id = Column(Integer, primary_key=True)


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
async def test_get_recommendations_by_user_id(db_session: AsyncSession):
    await create_recommendation_history(
        db_session,
        user_id=1,
        vehicle_id=1,
        hydrogen_station_id=1,
        recommendation_score=90.5,
        recommendation_reason="distance first",
        recommendation_type="AI",
    )

    rows = await get_recommendations(db_session, user_id=1)

    assert len(rows) == 1
    assert rows[0].user_id == 1
    assert float(rows[0].recommendation_score) == 90.5
