from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hydrogen_station_facilities import HydrogenStationAdditionalInfo
from app.models.hydrogen_station import HydrogenStation
from app.schemas.hydrogen_station_facilities_schema import (
    HydrogenStationAdditionalInfoCreate,
)


async def create_hydrogen_station_facility(
    db: AsyncSession,
    payload: HydrogenStationAdditionalInfoCreate,
) -> HydrogenStationAdditionalInfo:
    row = HydrogenStationAdditionalInfo(**payload.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def get_hydrogen_station_facilities(
    db: AsyncSession,
    chrstn_mno: str | None = None,
    adi_info_se_cd: str | None = None,
    del_at: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[HydrogenStationAdditionalInfo]:
    query = select(HydrogenStationAdditionalInfo)

    if chrstn_mno is not None:
        query = query.where(HydrogenStationAdditionalInfo.chrstn_mno == chrstn_mno)
    if adi_info_se_cd is not None:
        query = query.where(
            HydrogenStationAdditionalInfo.adi_info_se_cd == adi_info_se_cd
        )
    if del_at is not None:
        query = query.where(HydrogenStationAdditionalInfo.del_at == del_at)

    query = (
        query.order_by(HydrogenStationAdditionalInfo.additional_info_id.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def upsert_hydrogen_station_facilities(
    db: AsyncSession,
    payloads: list[HydrogenStationAdditionalInfoCreate],
) -> list[HydrogenStationAdditionalInfo]:
    rows: list[HydrogenStationAdditionalInfo] = []
    payloads = await _filter_payloads_with_existing_station(db, payloads)

    for payload in payloads:
        result = await db.execute(
            select(HydrogenStationAdditionalInfo)
            .where(HydrogenStationAdditionalInfo.chrstn_mno == payload.chrstn_mno)
            .where(
                HydrogenStationAdditionalInfo.adi_info_se_cd
                == payload.adi_info_se_cd
            )
            .limit(1)
        )
        row = result.scalar_one_or_none()
        values = payload.model_dump()

        if row is None:
            row = HydrogenStationAdditionalInfo(**values)
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
    payloads: list[HydrogenStationAdditionalInfoCreate],
) -> list[HydrogenStationAdditionalInfoCreate]:
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
