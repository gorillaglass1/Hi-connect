from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.charging_log import ChargingLog
from app.schemas.charging_log_schema import ChargingLogCreate


async def create_charging_logs(
    db: AsyncSession,
    payload: ChargingLogCreate,
) -> list[ChargingLog]:
    rows = [
        ChargingLog(
            user_id=payload.user_id,
            chrstn_mno=log.chrstn_mno,
            start_time=log.start_time,
            end_time=log.end_time,
            charged_amount=log.charged_amount,
            charging_cost=log.charging_cost,
            waiting_time=log.waiting_time,
        )
        for log in payload.logs
    ]
    db.add_all(rows)
    await db.commit()

    for row in rows:
        await db.refresh(row)

    return rows


async def get_charging_logs(
    db: AsyncSession,
    charging_log_id: int | None = None,
    user_id: int | None = None,
    chrstn_mno: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[ChargingLog]:
    query = select(ChargingLog)

    if charging_log_id is not None:
        query = query.where(ChargingLog.charging_log_id == charging_log_id)
    if user_id is not None:
        query = query.where(ChargingLog.user_id == user_id)
    if chrstn_mno is not None:
        query = query.where(ChargingLog.chrstn_mno == chrstn_mno)

    query = (
        query.order_by(ChargingLog.charging_log_id.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_recent_charging_logs_for_stations(
    db: AsyncSession,
    station_ids: list[str],
    limit: int = 1000,
) -> list[ChargingLog]:
    if not station_ids:
        return []

    query = (
        select(ChargingLog)
        .where(ChargingLog.chrstn_mno.in_(station_ids))
        .order_by(ChargingLog.start_time.desc(), ChargingLog.charging_log_id.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    return list(result.scalars().all())
