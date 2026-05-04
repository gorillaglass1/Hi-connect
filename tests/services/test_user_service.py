import pytest
import pytest_asyncio
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base
from app.models.user import User  # noqa: F401
from app.schemas.user_schema import UserCreate
from app.services.user_service import UserService

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
async def test_create_user_duplicate_email_raises_409(db_session):
    service = UserService(db_session)
    user = UserCreate(name="Seo", phone="010-1111-2222", email="seo@example.com")
    await service.create_user(user)

    with pytest.raises(HTTPException) as exc:
        await service.create_user(user)

    assert exc.value.status_code == 409
    assert exc.value.detail == "Email already exists"


@pytest.mark.asyncio
async def test_get_user_by_id_not_found_raises_404(db_session):
    service = UserService(db_session)

    with pytest.raises(HTTPException) as exc:
        await service.get_user_by_id(99999)

    assert exc.value.status_code == 404
    assert exc.value.detail == "User not found"


@pytest.mark.asyncio
async def test_update_user_success(db_session):
    service = UserService(db_session)
    created = await service.create_user(
        UserCreate(name="Seo", phone="010-1111-2222", email="seo@example.com")
    )

    updated = await service.update_user(
        created.user_id,
        name="Updated",
        phone="010-9999-0000",
    )

    assert updated.user_id == created.user_id
    assert updated.name == "Updated"
    assert updated.phone == "010-9999-0000"
    assert updated.email == "seo@example.com"


@pytest.mark.asyncio
async def test_update_user_missing_raises_404(db_session):
    service = UserService(db_session)

    with pytest.raises(HTTPException) as exc:
        await service.update_user(
            99999,
            name="No User",
        )

    assert exc.value.status_code == 404
    assert exc.value.detail == "User not found"
