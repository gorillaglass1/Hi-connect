import pytest
import pytest_asyncio
from sqlalchemy import Column, Integer
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from datetime import datetime, timedelta
from app.core.database import Base
from app.models.user import User  # noqa: F401
from app.repositories.charging_log_repo import (
    create_charging_log,
    get_charging_log_by_id,
    get_charging_logs
)


class HydrogenStation(Base):
    __tablename__ = "hydrogen_station"
    __table_args__ = {"extend_existing": True}
    hydrogen_station_id = Column(Integer, primary_key=True)


class Vehicle(Base):
    __tablename__ = "vehicles"
    __table_args__ = {"extend_existing": True}
    vehicle_id = Column(Integer, primary_key=True)

# 1. 엔진은 모듈 단위에서 한 번만 생성
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    # 테스트 시작 전 테이블 생성
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # 테스트 종료 후 테이블 삭제
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def db_session():
    async with TestingSessionLocal() as session:
        yield session
        # 테스트 종료 후 깔끔하게 롤백하여 데이터 격리
        await session.rollback()

@pytest.mark.asyncio
async def test_get_charging_logs_by_user_id(db_session):
    # Arrange: 데이터 선입력
    user_id = 99
    # 주의: 순차적으로 생성하여 시간 차이를 명확히 함
    now = datetime.now()
    for i in range(3):
        await create_charging_log(
            db_session, 
            user_id=user_id, 
            hydrogen_station_id=1, 
            vehicle_id=1,
            # i가 커질수록 더 과거의 시간이 됨
            start_time=now - timedelta(days=i),
            end_time=now - timedelta(days=i, hours=-1), 
            charged_amount=1.0, 
            charging_cost=100, 
            waiting_time=5
        )

    # Act
    logs = await get_charging_logs(db_session, user_id=user_id)

    # Assert
    assert len(logs) == 3
    # 리포지토리 로직에 desc()가 있다면 0번 인덱스가 가장 최신(큰 값)이어야 함
    assert logs[0].start_time > logs[1].start_time 
    assert logs[1].start_time > logs[2].start_time
