import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base
from app.models.user import User  # noqa: F401
from app.repositories.user_repo import create_user, update_user

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
async def test_update_user_success(db_session):
    created = await create_user(
        db_session,
        name="Seo",
        email="seo@example.com",
        phone="010-1111-2222",
    )

    updated = await update_user(
        db_session,
        user_id=created.user_id,
        name="Seo Updated",
        phone="010-9999-0000",
    )

    assert updated is not None
    assert updated.user_id == created.user_id
    assert updated.name == "Seo Updated"
    assert updated.phone == "010-9999-0000"
    assert updated.email == "seo@example.com"


@pytest.mark.asyncio
async def test_update_user_not_found_returns_none(db_session):
    updated = await update_user(
        db_session,
        user_id=99999,
        name="No User",
    )

    assert updated is None
