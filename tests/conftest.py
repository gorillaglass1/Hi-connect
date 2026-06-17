import os

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

TEST_DB_PATH = "./test_hydrogen_station_api.db"
TEST_DB_URL = f"sqlite+aiosqlite:///{TEST_DB_PATH}"

os.environ["DATABASE_URL"] = TEST_DB_URL
os.environ["SUPABASE_DB_URL"] = ""
os.environ["SUPABASE_DB_HOST"] = ""
os.environ["SUPABASE_DB_PASSWORD"] = ""
os.environ["HYING_STARTUP_SYNC_ENABLED"] = "false"
os.environ["HYING_STATUS_SYNC_ENABLED"] = "false"
# Keep tests offline/deterministic: never hit the Gemini API for reason generation.
os.environ["GEMINI_API_KEY"] = ""
os.environ["GOOGLE_API_KEY"] = ""

from app.core.database import Base, get_db  # noqa: E402
from index import app  # noqa: E402


@pytest_asyncio.fixture(scope="session")
async def engine():
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

    test_engine = create_async_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
    )

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield test_engine

    await test_engine.dispose()
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)


@pytest_asyncio.fixture
async def db_session(engine) -> AsyncSession:
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )
    async with session_factory() as session:
        yield session


@pytest.fixture
def client(db_session: AsyncSession):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
