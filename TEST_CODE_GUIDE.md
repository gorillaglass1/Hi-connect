Recommendation_history

```sql
CREATE TABLE recommendation_history (

    recommendation_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    -- 추천 기록 고유 ID

    user_id BIGINT NOT NULL,
    -- 추천을 받은 사용자 ID

    vehicle_id BIGINT NOT NULL,
    -- 추천 당시 사용된 차량 ID

    hydrogen_station_id BIGINT NOT NULL,
    -- 추천된 충전소 ID

    recommendation_score DECIMAL(5,2),
    -- 추천 점수 (AI 추천 점수 / 우선순위)

    recommendation_reason VARCHAR(255),
    -- 추천 이유 (예: 거리 우선, 대기시간 짧음, 잔여 수소 충분)

    user_latitude DECIMAL(10,7),
    -- 추천 시점 사용자 위도

    user_longitude DECIMAL(10,7),
    -- 추천 시점 사용자 경도

    vehicle_remaining_hydrogen DECIMAL(6,2),
    -- 추천 시점 차량 수소 잔량 (kg)

    estimated_arrival_time INT,
    -- 충전소까지 예상 이동 시간 (분)

    estimated_wait_time INT,
    -- 추천 당시 예상 대기시간 (분)

    selected BOOLEAN DEFAULT FALSE,
    -- 사용자가 실제 해당 충전소를 선택했는지 여부

    selected_at DATETIME,
    -- 실제 선택 시간

    recommendation_type VARCHAR(50),
    -- 추천 방식 (AI / 거리기반 / 혼잡도 기반 등)

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- 추천 생성 시각

		CONSTRAINT fk_history_users FOREIGN KEY (user_id) REFERENCES users(user_id),
		CONSTRAINT fk_history_vehicle FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id),
		CONSTRAINT fk_history_station FOREIGN KEY (hydrogen_station_id) REFERENCES hydrogen_station(hydrogen_station_id)

);
```

```sql
INSERT INTO recommendation_history (
    user_id,
    vehicle_id,
    hydrogen_station_id,
    recommendation_score,
    recommendation_reason,
    user_latitude,
    user_longitude,
    vehicle_remaining_hydrogen,
    estimated_arrival_time,
    estimated_wait_time,
    selected,
    selected_at,
    recommendation_type
) VALUES
(
    1,
    1,
    3,
    92.50,
    '가장 가까우며 대기시간이 짧은 충전소',
    37.5665000,
    126.9780000,
    2.80,
    8,
    5,
    TRUE,
    '2026-04-27 14:12:00',
    'AI'
),
(
    2,
    2,
    5,
    85.30,
    '수소 재고가 충분하고 혼잡도가 낮음',
    37.3943000,
    127.1112000,
    1.40,
    12,
    3,
    FALSE,
    NULL,
    'WAIT_TIME'
),
(
    3,
    4,
    2,
    78.90,
    '거리 대비 효율이 좋은 충전소 추천',
    35.1796000,
    129.0756000,
    0.95,
    18,
    10,
    TRUE,
    '2026-04-27 15:45:00',
    'DISTANCE'
);
```

hydrogen_station_realtime

```sql
CREATE TABLE hydrogen_station_realtime (

    realtime_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    -- 실시간 상태 고유 ID

    hydrogen_station_id BIGINT NOT NULL,
    -- 충전소 ID (station 테이블 FK)

    available_chargers INT DEFAULT 0,
    -- 현재 사용 가능한 충전기 수

    in_use_chargers INT DEFAULT 0,
    -- 현재 사용 중인 충전기 수

    queue_count INT DEFAULT 0,
    -- 현재 대기 차량 수

    avg_wait_time INT,
    -- 평균 예상 대기시간 (분)

    hydrogen_stock_kg DECIMAL(8,2),
    -- 충전소 내 남은 수소 총량 (kg)

    station_status VARCHAR(50),
    -- 충전소 상태 (운영중 / 점검중 / 재고부족 / 혼잡 등)

    last_restock_at DATETIME,
    -- 마지막 수소 보충 시각

    next_restock_schedule DATETIME,
    -- 다음 수소 보충 예정 시각

    utilization_rate DECIMAL(5,2),
    -- 충전소 사용률 (%)

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,
    -- 실시간 데이터 갱신 시각

	CONSTRAINT fk_realtime_station FOREIGN KEY (hydrogen_station_id) REFERENCES hydrogen_station(hydrogen_station_id)

);
```

```sql
INSERT INTO hydrogen_station_realtime (
    hydrogen_station_id,
    available_chargers,
    in_use_chargers,
    queue_count,
    avg_wait_time,
    hydrogen_stock_kg,
    station_status,
    last_restock_at,
    next_restock_schedule,
    utilization_rate
) VALUES
(
    1,
    2,
    3,
    4,
    12,
    185.50,
    'BUSY',
    '2026-04-27 06:30:00',
    '2026-04-27 18:00:00',
    60.00
),
(
    2,
    4,
    1,
    0,
    3,
    320.75,
    'AVAILABLE',
    '2026-04-27 08:00:00',
    '2026-04-28 08:00:00',
    20.00
),
(
    3,
    0,
    5,
    8,
    25,
    42.30,
    'LOW_HYDROGEN',
    '2026-04-26 22:15:00',
    '2026-04-27 12:30:00',
    100.00
);
```

hydrogen_station_reservation

```sql
CREATE TABLE hydrogen_station_reservation (
	hydrogen_station_reservation_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    hydrogen_charger_id BIGINT NOT NULL, -- 충전기 foreign key
    hydrogen_station_id BIGINT NOT NULL, -- 충전소 foreign key
    reservation_status ENUM('RESERVED', 'CANCELLED', 'COMPLETED', 'EXPIRED') NOT NULL, -- 예약 상태
    user_id BIGINT NOT NULL, -- user foreign key
    reservation_time DATETIME NOT NULL, -- 예약 시작 시간
    expire_time DATETIME NOT NULL, -- 예약 종료 시간 
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP, -- 예약 생성 시간
    
    CONSTRAINT fk_reservation_charger FOREIGN KEY (hydrogen_charger_id) REFERENCES hydrogen_charger(hydrogen_charger_id),
    CONSTRAINT fk_reservation_station FOREIGN KEY (hydrogen_station_id) REFERENCES hydrogen_station(hydrogen_station_id),
    CONSTRAINT fk_reservation_users FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

```sql
INSERT INTO hydrogen_station_reservation (
    hydrogen_charger_id,
    hydrogen_station_id,
    reservation_status,
    user_id,
    reservation_time,
    expire_time
) VALUES
(
    1,
    1,
    'RESERVED',
    1,
    '2026-04-27 18:00:00',
    '2026-04-27 18:30:00'
),
(
    2,
    1,
    'COMPLETED',
    2,
    '2026-04-27 14:20:00',
    '2026-04-27 14:50:00'
),
(
    3,
    2,
    'EXPIRED',
    3,
    '2026-04-27 15:00:00',
    '2026-04-27 15:20:00'
);
```

---

## Recommendation_history - Entity

```python
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    func,
)

from app.core.database import Base


class RecommendationHistory(Base):
    __tablename__ = "recommendation_history"

    recommendation_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    vehicle_id = Column(Integer, ForeignKey("vehicles.vehicle_id"), nullable=False)
    hydrogen_station_id = Column(
        Integer, ForeignKey("hydrogen_station.hydrogen_station_id"), nullable=False
    )
    recommendation_score = Column(Numeric(5, 2))
    recommendation_reason = Column(String(255))
    user_latitude = Column(Numeric(10, 7))
    user_longitude = Column(Numeric(10, 7))
    vehicle_remaining_hydrogen = Column(Numeric(6, 2))
    estimated_arrival_time = Column(Integer)
    estimated_wait_time = Column(Integer)
    selected = Column(Boolean, default=False)
    selected_at = Column(DateTime)
    recommendation_type = Column(String(50))
    created_at = Column(DateTime, server_default=func.now())
```

## Recommendation_history - Repository

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recommendation_history import RecommendationHistory


async def create_recommendation_history(
    db: AsyncSession,
    user_id: int,
    vehicle_id: int,
    hydrogen_station_id: int,
    recommendation_score: float,
    recommendation_reason: str | None,
    recommendation_type: str | None,
):
    row = RecommendationHistory(
        user_id=user_id,
        vehicle_id=vehicle_id,
        hydrogen_station_id=hydrogen_station_id,
        recommendation_score=recommendation_score,
        recommendation_reason=recommendation_reason,
        recommendation_type=recommendation_type,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def get_recommendations_by_user_id(
    db: AsyncSession, user_id: int, limit: int = 20, offset: int = 0
):
    result = await db.execute(
        select(RecommendationHistory)
        .where(RecommendationHistory.user_id == user_id)
        .order_by(RecommendationHistory.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return result.scalars().all()
```

## Recommendation_history - 테스트 코드

```python
import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.recommendation_history_repo import (
    create_recommendation_history,
    get_recommendations_by_user_id,
)


@pytest.mark.asyncio
async def test_get_recommendations_by_user_id(db_session: AsyncSession):
    await create_recommendation_history(
        db_session,
        user_id=1,
        vehicle_id=1,
        hydrogen_station_id=1,
        recommendation_score=90.5,
        recommendation_reason="거리 우선",
        recommendation_type="AI",
    )

    rows = await get_recommendations_by_user_id(db_session, user_id=1)

    assert len(rows) >= 1
    assert rows[0].user_id == 1
```

## hydrogen_station_realtime - Entity

```python
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, func

from app.core.database import Base


class HydrogenStationRealtime(Base):
    __tablename__ = "hydrogen_station_realtime"

    realtime_id = Column(Integer, primary_key=True, autoincrement=True)
    hydrogen_station_id = Column(
        Integer, ForeignKey("hydrogen_station.hydrogen_station_id"), nullable=False
    )
    available_chargers = Column(Integer, default=0)
    in_use_chargers = Column(Integer, default=0)
    queue_count = Column(Integer, default=0)
    avg_wait_time = Column(Integer)
    hydrogen_stock_kg = Column(Numeric(8, 2))
    station_status = Column(String(50))
    last_restock_at = Column(DateTime)
    next_restock_schedule = Column(DateTime)
    utilization_rate = Column(Numeric(5, 2))
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
```

## hydrogen_station_realtime - Repository

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hydrogen_station_realtime import HydrogenStationRealtime


async def upsert_station_realtime(
    db: AsyncSession,
    hydrogen_station_id: int,
    queue_count: int,
    avg_wait_time: int,
    station_status: str,
):
    result = await db.execute(
        select(HydrogenStationRealtime).where(
            HydrogenStationRealtime.hydrogen_station_id == hydrogen_station_id
        )
    )
    row = result.scalars().first()

    if row is None:
        row = HydrogenStationRealtime(
            hydrogen_station_id=hydrogen_station_id,
            queue_count=queue_count,
            avg_wait_time=avg_wait_time,
            station_status=station_status,
        )
        db.add(row)
    else:
        row.queue_count = queue_count
        row.avg_wait_time = avg_wait_time
        row.station_status = station_status

    await db.commit()
    await db.refresh(row)
    return row


async def get_realtime_by_station_id(db: AsyncSession, hydrogen_station_id: int):
    result = await db.execute(
        select(HydrogenStationRealtime).where(
            HydrogenStationRealtime.hydrogen_station_id == hydrogen_station_id
        )
    )
    return result.scalars().first()
```

## hydrogen_station_realtime - 테스트 코드

```python
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.hydrogen_station_realtime_repo import (
    get_realtime_by_station_id,
    upsert_station_realtime,
)


@pytest.mark.asyncio
async def test_upsert_station_realtime(db_session: AsyncSession):
    first = await upsert_station_realtime(
        db_session, hydrogen_station_id=1, queue_count=3, avg_wait_time=10, station_status="BUSY"
    )
    second = await upsert_station_realtime(
        db_session, hydrogen_station_id=1, queue_count=1, avg_wait_time=4, station_status="AVAILABLE"
    )

    row = await get_realtime_by_station_id(db_session, hydrogen_station_id=1)

    assert first.realtime_id == second.realtime_id
    assert row.queue_count == 1
    assert row.station_status == "AVAILABLE"
```

## hydrogen_station_reservation - Entity

```python
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func

from app.core.database import Base


class HydrogenStationReservation(Base):
    __tablename__ = "hydrogen_station_reservation"

    hydrogen_station_reservation_id = Column(Integer, primary_key=True, autoincrement=True)
    hydrogen_charger_id = Column(
        Integer, ForeignKey("hydrogen_charger.hydrogen_charger_id"), nullable=False
    )
    hydrogen_station_id = Column(
        Integer, ForeignKey("hydrogen_station.hydrogen_station_id"), nullable=False
    )
    reservation_status = Column(String(20), nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    reservation_time = Column(DateTime, nullable=False)
    expire_time = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
```

## hydrogen_station_reservation - Repository

```python
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hydrogen_station_reservation import HydrogenStationReservation


async def create_reservation(
    db: AsyncSession,
    hydrogen_charger_id: int,
    hydrogen_station_id: int,
    user_id: int,
    reservation_time: datetime,
    expire_time: datetime,
):
    row = HydrogenStationReservation(
        hydrogen_charger_id=hydrogen_charger_id,
        hydrogen_station_id=hydrogen_station_id,
        reservation_status="RESERVED",
        user_id=user_id,
        reservation_time=reservation_time,
        expire_time=expire_time,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def get_active_reservations_by_station(
    db: AsyncSession, hydrogen_station_id: int
):
    result = await db.execute(
        select(HydrogenStationReservation).where(
            HydrogenStationReservation.hydrogen_station_id == hydrogen_station_id,
            HydrogenStationReservation.reservation_status == "RESERVED",
        )
    )
    return result.scalars().all()
```

## hydrogen_station_reservation - 테스트 코드

```python
import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.hydrogen_station_reservation_repo import (
    create_reservation,
    get_active_reservations_by_station,
)


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

    rows = await get_active_reservations_by_station(db_session, hydrogen_station_id=1)

    assert len(rows) >= 1
    assert rows[0].reservation_status == "RESERVED"
```
