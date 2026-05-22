from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hydrogen_stations import HydrogenStation
from app.models.hydrogen_station_status import HydrogenStationStatus
from app.schemas.hydrogen_station_status_schemas import HydrogenStationStatusCreate


async def create_hydrogen_station_status(
    db: AsyncSession,
    payload: HydrogenStationStatusCreate,
) -> HydrogenStationStatus:
    row = HydrogenStationStatus(**payload.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def get_hydrogen_station_statuses(
    db: AsyncSession,
    chrstn_mno: str | None = None,
    oper_sttus_cd: str | None = None,
    pos_sttus_cd: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[HydrogenStationStatus]:
    query = select(HydrogenStationStatus)

    if chrstn_mno is not None:
        query = query.where(HydrogenStationStatus.chrstn_mno == chrstn_mno)
    if oper_sttus_cd is not None:
        query = query.where(HydrogenStationStatus.oper_sttus_cd == oper_sttus_cd)
    if pos_sttus_cd is not None:
        query = query.where(HydrogenStationStatus.pos_sttus_cd == pos_sttus_cd)

    query = (
        query.order_by(HydrogenStationStatus.last_mdfcn_dt.desc().nullslast())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_latest_hydrogen_station_status(
    db: AsyncSession,
    chrstn_mno: str,
) -> HydrogenStationStatus | None:
    result = await db.execute(
        select(HydrogenStationStatus)
        .where(HydrogenStationStatus.chrstn_mno == chrstn_mno)
        .order_by(
            HydrogenStationStatus.last_mdfcn_dt.desc().nullslast(),
            HydrogenStationStatus.status_id.desc(),
        )
        .limit(1)
    )
    return result.scalar_one_or_none()


async def upsert_hydrogen_station_statuses(
    db: AsyncSession,
    payloads: list[HydrogenStationStatusCreate],
) -> list[HydrogenStationStatus]:
    rows: list[HydrogenStationStatus] = []
    payloads = await _filter_payloads_with_existing_station(db, payloads)

    for payload in payloads:
        result = await db.execute(
            select(HydrogenStationStatus)
            .where(HydrogenStationStatus.chrstn_mno == payload.chrstn_mno)
            .order_by(HydrogenStationStatus.status_id.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        values = payload.model_dump()

        if row is None:
            row = HydrogenStationStatus(**values)
            db.add(row)
        else:
            for key, value in values.items():
                setattr(row, key, value)

        rows.append(row)

    await db.commit()

    for row in rows:
        await db.refresh(row)

    return rows


async def _filter_payloads_with_existing_station(
    db: AsyncSession,
    payloads: list[HydrogenStationStatusCreate],
) -> list[HydrogenStationStatusCreate]:
    if not payloads:
        return []

    station_ids = {payload.chrstn_mno for payload in payloads}
    result = await db.execute(
        select(HydrogenStation.chrstn_mno).where(
            HydrogenStation.chrstn_mno.in_(station_ids)
        )
    )
    existing_station_ids = set(result.scalars().all())
    return [
        payload
        for payload in payloads
        if payload.chrstn_mno in existing_station_ids
    ]
