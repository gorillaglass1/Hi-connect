from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager, joinedload, selectinload

from app.models.hydrogen_station_facilities import HydrogenStationAdditionalInfo
from app.models.hydrogen_station_status import HydrogenStationStatus
from app.models.hydrogen_station import HydrogenStation
from app.schemas.hydrogen_station_schema import HydrogenStationCreate


async def create_hydrogen_station(
    db: AsyncSession,
    payload: HydrogenStationCreate,
) -> HydrogenStation:
    row = HydrogenStation(**payload.model_dump())
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def get_hydrogen_station_by_id(
    db: AsyncSession,
    chrstn_mno: str,
) -> HydrogenStation | None:
    result = await db.execute(
        select(HydrogenStation).where(HydrogenStation.chrstn_mno == chrstn_mno)
    )
    return result.scalar_one_or_none()


async def get_hydrogen_stations(
    db: AsyncSession,
    chrstn_mno: str | None = None,
    chrstn_nm: str | None = None,
    oper_yn: str | None = None,
    rltm_info_yn: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[HydrogenStation]:
    query = select(HydrogenStation)

    if chrstn_mno is not None:
        query = query.where(HydrogenStation.chrstn_mno == chrstn_mno)
    if chrstn_nm:
        query = query.where(HydrogenStation.chrstn_nm.ilike(f"%{chrstn_nm}%"))
    if oper_yn is not None:
        query = query.where(HydrogenStation.oper_yn == oper_yn)
    if rltm_info_yn is not None:
        query = query.where(HydrogenStation.rltm_info_yn == rltm_info_yn)

    query = query.order_by(HydrogenStation.chrstn_nm.asc()).limit(limit).offset(offset)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_hydrogen_station_detail_by_id(
    db: AsyncSession,
    chrstn_mno: str,
) -> HydrogenStation | None:
    latest_status_id_subquery = (
        select(HydrogenStationStatus.status_id)
        .where(HydrogenStationStatus.chrstn_mno == chrstn_mno)
        .order_by(
            HydrogenStationStatus.last_mdfcn_dt.desc().nullslast(),
            HydrogenStationStatus.status_id.desc(),
        )
        .limit(1)
        .scalar_subquery()
    )
    query = (
        select(HydrogenStation)
        .outerjoin(
            HydrogenStationStatus,
            HydrogenStationStatus.status_id == latest_status_id_subquery,
        )
        .options(
            contains_eager(HydrogenStation.status_list),
            joinedload(HydrogenStation.facilities_list),
        )
        .where(HydrogenStation.chrstn_mno == chrstn_mno)
    )
    result = await db.execute(query)
    return result.unique().scalar_one_or_none()


async def get_hydrogen_station_details(
    db: AsyncSession,
    chrstn_mno: str | None = None,
    chrstn_nm: str | None = None,
    address: str | None = None,
    oper_yn: str | None = None,
    rltm_info_yn: str | None = None,
    rsvt_posbl_yn: str | None = None,
    oper_sttus_nm: str | None = None,
    pos_sttus_nm: str | None = None,
    cnf_sttus_nm: str | None = None,
    facility_nm: str | None = None,
    sort_by: str | None = None,
    sort_order: str = "asc",
    limit: int = 100,
    offset: int = 0,
) -> list[HydrogenStation]:
    latest_status_id_subquery = (
        select(HydrogenStationStatus.status_id)
        .where(HydrogenStationStatus.chrstn_mno == HydrogenStation.chrstn_mno)
        .order_by(
            HydrogenStationStatus.last_mdfcn_dt.desc().nullslast(),
            HydrogenStationStatus.status_id.desc(),
        )
        .limit(1)
        .correlate(HydrogenStation)
        .scalar_subquery()
    )
    query = (
        select(HydrogenStation)
        .outerjoin(
            HydrogenStationStatus,
            HydrogenStationStatus.status_id == latest_status_id_subquery,
        )
        .options(
            contains_eager(HydrogenStation.status_list),
            joinedload(HydrogenStation.facilities_list),
        )
    )

    if chrstn_mno is not None:
        query = query.where(HydrogenStation.chrstn_mno == chrstn_mno)
    if chrstn_nm:
        query = query.where(HydrogenStation.chrstn_nm.ilike(f"%{chrstn_nm}%"))
    if address:
        query = query.where(
            or_(
                HydrogenStation.road_nm_addr.ilike(f"{address}%"),
                HydrogenStation.lotno_addr.ilike(f"{address}%"),
            )
        )
    if oper_yn is not None:
        query = query.where(HydrogenStation.oper_yn == oper_yn)
    if rltm_info_yn is not None:
        query = query.where(HydrogenStation.rltm_info_yn == rltm_info_yn)
    if rsvt_posbl_yn is not None:
        query = query.where(HydrogenStation.rsvt_posbl_yn == rsvt_posbl_yn)
    if oper_sttus_nm:
        query = query.where(HydrogenStationStatus.oper_sttus_nm.ilike(f"%{oper_sttus_nm}%"))
    if pos_sttus_nm:
        query = query.where(HydrogenStationStatus.pos_sttus_nm.ilike(f"%{pos_sttus_nm}%"))
    if cnf_sttus_nm:
        query = query.where(HydrogenStationStatus.cnf_sttus_nm.ilike(f"%{cnf_sttus_nm}%"))
    if facility_nm:
        query = query.where(
            HydrogenStation.facilities_list.any(
                HydrogenStationAdditionalInfo.adi_info_se_nm.ilike(f"%{facility_nm}%")
            )
        )

    order_columns = {
        "chrstn_nm": HydrogenStation.chrstn_nm,
        "wait_vhcle_alge": HydrogenStationStatus.wait_vhcle_alge,
        "prfect_elctc_posbl_alge": HydrogenStationStatus.prfect_elctc_posbl_alge,
        "tt_pressr": HydrogenStationStatus.tt_pressr,
    }
    order_column = order_columns.get(sort_by or "chrstn_nm", HydrogenStation.chrstn_nm)
    order_expression = order_column.desc() if sort_order == "desc" else order_column.asc()
    query = query.order_by(
        order_expression.nullslast(),
        HydrogenStation.chrstn_nm.asc(),
    ).limit(limit).offset(offset)
    result = await db.execute(query)
    return list(result.unique().scalars().all())


async def get_active_hydrogen_stations_for_recommendation(
    db: AsyncSession,
    candidate_station_ids: list[str] | None = None,
) -> list[HydrogenStation]:
    query = (
        select(HydrogenStation)
        .where(HydrogenStation.oper_yn == "Y")
        .where(HydrogenStation.del_at == "0")
        .options(
            selectinload(HydrogenStation.status_list),
            selectinload(HydrogenStation.facilities_list),
        )
    )

    if candidate_station_ids is not None:
        query = query.where(HydrogenStation.chrstn_mno.in_(candidate_station_ids))

    result = await db.execute(query)
    return list(result.scalars().all())


async def upsert_hydrogen_stations(
    db: AsyncSession,
    payloads: list[HydrogenStationCreate],
) -> list[HydrogenStation]:
    rows: list[HydrogenStation] = []

    for payload in payloads:
        row = await get_hydrogen_station_by_id(db, payload.chrstn_mno)
        values = payload.model_dump()

        if row is None:
            row = HydrogenStation(**values)
            db.add(row)
        else:
            for key, value in values.items():
                setattr(row, key, value)

        rows.append(row)

    await db.commit()

    for row in rows:
        await db.refresh(row)

    return rows
