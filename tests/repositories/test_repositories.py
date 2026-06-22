from datetime import datetime
from decimal import Decimal

import pytest

from app.repositories import (
    charging_log_repo,
    hydrogen_station_facilities_repo,
    hydrogen_station_repo,
    hydrogen_station_status_repo,
    recommendation_history_repo,
    user_preference_repo,
)
from app.schemas.charging_log_schema import ChargingLogCreate, ChargingLogItemCreate
from app.schemas.hydrogen_station_facilities_schema import (
    HydrogenStationAdditionalInfoCreate,
)
from app.schemas.hydrogen_station_schema import HydrogenStationCreate
from app.schemas.hydrogen_station_status_schema import HydrogenStationStatusCreate
from app.schemas.recommendation_history_schema import (
    RecommendationHistoryCreate,
    RecommendationStationCreate,
)
from app.schemas.user_preference_schema import UserCreate, UserPreferenceUpdate


async def _create_station(db_session, station_id: str, **overrides):
    payload = {
        "chrstn_mno": station_id,
        "chrstn_nm": overrides.pop("chrstn_nm", f"{station_id} 충전소"),
        "road_nm_addr": overrides.pop("road_nm_addr", "인천광역시 남동구"),
        "lotno_addr": overrides.pop("lotno_addr", "인천광역시 남동구 구월동"),
        "oper_yn": overrides.pop("oper_yn", "Y"),
        "del_at": overrides.pop("del_at", "0"),
        "rltm_info_yn": overrides.pop("rltm_info_yn", "Y"),
        "lon": overrides.pop("lon", Decimal("126.7000")),
        "let": overrides.pop("let", Decimal("37.4100")),
    }
    payload.update(overrides)
    return await hydrogen_station_repo.create_hydrogen_station(
        db_session,
        HydrogenStationCreate(**payload),
    )


@pytest.mark.asyncio
async def test_user_preference_repo_create_get_and_update_round_trip(db_session):
    user = await user_preference_repo.create_user(
        db_session,
        UserCreate(
            name="Repo User",
            phone="010-1000-0001",
            email="repo-user-0001@example.com",
        ),
    )

    pref = await user_preference_repo.create_user_preferences(
        db_session,
        user.user_id,
        UserPreferenceUpdate(
            weight_price=Decimal("2.00"),
            weight_waiting_time=Decimal("1.50"),
            weight_distance=Decimal("0.40"),
            weight_facilities=Decimal("0.10"),
            safety_margin=Decimal("1.20"),
        ),
    )
    updated = await user_preference_repo.update_user_preferences(
        db_session,
        pref,
        UserPreferenceUpdate(
            weight_price=Decimal("1.25"),
            weight_waiting_time=Decimal("1.75"),
            weight_distance=Decimal("0.75"),
            weight_facilities=Decimal("0.25"),
            safety_margin=Decimal("1.15"),
        ),
    )
    loaded_user = await user_preference_repo.get_user(db_session, user.user_id)
    loaded_pref = await user_preference_repo.get_user_preferences(
        db_session,
        user.user_id,
    )

    assert updated.weight_price == Decimal("1.25")
    assert loaded_pref.weight_waiting_time == Decimal("1.75")
    assert loaded_user.preferences.user_id == user.user_id


@pytest.mark.asyncio
async def test_hydrogen_station_repo_filters_orders_and_upserts(db_session):
    await _create_station(
        db_session,
        "REPO-ST-001",
        chrstn_nm="가나다 충전소",
        road_nm_addr="인천광역시 미추홀구",
        oper_yn="Y",
    )
    await _create_station(
        db_session,
        "REPO-ST-002",
        chrstn_nm="라마바 충전소",
        road_nm_addr="서울특별시 강남구",
        oper_yn="N",
    )

    operating = await hydrogen_station_repo.get_hydrogen_stations(
        db_session,
        chrstn_nm="가나다",
        oper_yn="Y",
    )
    assert [station.chrstn_mno for station in operating] == ["REPO-ST-001"]

    upserted = await hydrogen_station_repo.upsert_hydrogen_stations(
        db_session,
        [
            HydrogenStationCreate(
                chrstn_mno="REPO-ST-001",
                chrstn_nm="수정된 충전소",
                road_nm_addr="인천광역시 연수구",
                oper_yn="Y",
            ),
            HydrogenStationCreate(
                chrstn_mno="REPO-ST-003",
                chrstn_nm="신규 충전소",
                road_nm_addr="인천광역시 부평구",
                oper_yn="Y",
            ),
        ],
    )

    assert len(upserted) == 2
    loaded = await hydrogen_station_repo.get_hydrogen_station_by_id(
        db_session,
        "REPO-ST-001",
    )
    assert loaded.chrstn_nm == "수정된 충전소"
    assert loaded.road_nm_addr == "인천광역시 연수구"


@pytest.mark.asyncio
async def test_active_hydrogen_station_repo_filters_deleted_closed_and_candidates(
    db_session,
):
    await _create_station(db_session, "REPO-ACTIVE-001", oper_yn="Y", del_at="0")
    await _create_station(db_session, "REPO-ACTIVE-002", oper_yn="N", del_at="0")
    await _create_station(db_session, "REPO-ACTIVE-003", oper_yn="Y", del_at="1")

    active = await hydrogen_station_repo.get_active_hydrogen_stations_for_recommendation(
        db_session,
        candidate_station_ids=["REPO-ACTIVE-001", "REPO-ACTIVE-002", "MISSING"],
    )

    assert [station.chrstn_mno for station in active] == ["REPO-ACTIVE-001"]


@pytest.mark.asyncio
async def test_active_hydrogen_station_repo_loads_only_latest_status(
    db_session,
):
    await _create_station(db_session, "REPO-ACTIVE-LATEST-STATUS")
    await hydrogen_station_status_repo.create_hydrogen_station_status(
        db_session,
        HydrogenStationStatusCreate(
            chrstn_mno="REPO-ACTIVE-LATEST-STATUS",
            wait_vhcle_alge=5,
            last_mdfcn_dt="20260524090000",
        ),
    )
    await hydrogen_station_status_repo.create_hydrogen_station_status(
        db_session,
        HydrogenStationStatusCreate(
            chrstn_mno="REPO-ACTIVE-LATEST-STATUS",
            wait_vhcle_alge=1,
            last_mdfcn_dt="20260524100000",
        ),
    )

    active = await hydrogen_station_repo.get_active_hydrogen_stations_for_recommendation(
        db_session,
        candidate_station_ids=["REPO-ACTIVE-LATEST-STATUS"],
    )

    assert len(active) == 1
    assert [status.wait_vhcle_alge for status in active[0].status_list] == [1]


@pytest.mark.asyncio
async def test_status_repo_upserts_only_existing_stations_and_returns_latest(
    db_session,
):
    await _create_station(db_session, "REPO-STATUS-001")
    await hydrogen_station_status_repo.create_hydrogen_station_status(
        db_session,
        HydrogenStationStatusCreate(
            chrstn_mno="REPO-STATUS-001",
            wait_vhcle_alge=5,
            oper_sttus_cd="OLD",
            last_mdfcn_dt="20260524090000",
        ),
    )
    await hydrogen_station_status_repo.create_hydrogen_station_status(
        db_session,
        HydrogenStationStatusCreate(
            chrstn_mno="REPO-STATUS-001",
            wait_vhcle_alge=1,
            oper_sttus_cd="NEW",
            last_mdfcn_dt="20260524100000",
        ),
    )

    upserted = await hydrogen_station_status_repo.upsert_hydrogen_station_statuses(
        db_session,
        [
            HydrogenStationStatusCreate(
                chrstn_mno="REPO-STATUS-001",
                wait_vhcle_alge=3,
                oper_sttus_cd="UPDATED",
                last_mdfcn_dt="20260524110000",
            ),
            HydrogenStationStatusCreate(
                chrstn_mno="REPO-STATUS-MISSING",
                wait_vhcle_alge=9,
                oper_sttus_cd="SKIPPED",
            ),
        ],
    )
    latest = await hydrogen_station_status_repo.get_latest_hydrogen_station_status(
        db_session,
        "REPO-STATUS-001",
    )
    filtered = await hydrogen_station_status_repo.get_hydrogen_station_statuses(
        db_session,
        chrstn_mno="REPO-STATUS-001",
        oper_sttus_cd="UPDATED",
    )

    assert len(upserted) == 1
    assert latest.oper_sttus_cd == "UPDATED"
    assert latest.wait_vhcle_alge == 3
    assert len(filtered) == 1


@pytest.mark.asyncio
async def test_facility_repo_upserts_only_existing_stations_and_filters(db_session):
    await _create_station(db_session, "REPO-FAC-001")

    created = await hydrogen_station_facilities_repo.create_hydrogen_station_facility(
        db_session,
        HydrogenStationAdditionalInfoCreate(
            chrstn_mno="REPO-FAC-001",
            adi_info_se_cd="CVS",
            adi_info_se_nm="편의점",
        ),
    )
    upserted = await hydrogen_station_facilities_repo.upsert_hydrogen_station_facilities(
        db_session,
        [
            HydrogenStationAdditionalInfoCreate(
                chrstn_mno="REPO-FAC-001",
                adi_info_se_cd="CVS",
                adi_info_se_nm="무인 편의점",
            ),
            HydrogenStationAdditionalInfoCreate(
                chrstn_mno="REPO-FAC-MISSING",
                adi_info_se_cd="CAFE",
                adi_info_se_nm="카페",
            ),
        ],
    )
    filtered = await hydrogen_station_facilities_repo.get_hydrogen_station_facilities(
        db_session,
        chrstn_mno="REPO-FAC-001",
        adi_info_se_cd="CVS",
        del_at="0",
    )

    assert created.additional_info_id == upserted[0].additional_info_id
    assert len(upserted) == 1
    assert filtered[0].adi_info_se_nm == "무인 편의점"


@pytest.mark.asyncio
async def test_recommendation_history_repo_filters_latest_snapshot_and_selection(
    db_session,
):
    await _create_station(db_session, "REPO-HIST-001")
    rows = await recommendation_history_repo.create_recommendation_histories(
        db_session,
        RecommendationHistoryCreate(
            user_id=777,
            user_latitude=Decimal("37.405"),
            user_longitude=Decimal("126.721"),
            vehicle_remaining_hydrogen=Decimal("45.00"),
            recommendations=[
                RecommendationStationCreate(
                    chrstn_mno="REPO-HIST-001",
                    recommendation_score=Decimal("70.0"),
                    recommendation_type="PERSONALIZED",
                ),
                RecommendationStationCreate(
                    chrstn_mno="REPO-HIST-001",
                    recommendation_score=Decimal("95.0"),
                    price_score=Decimal("90"),
                    waiting_time_score=Decimal("80"),
                    distance_score=Decimal("70"),
                    facilities_score=Decimal("60"),
                    recommendation_type="SEMANTIC_AI",
                ),
            ],
        ),
    )

    latest = await recommendation_history_repo.get_latest_recommendation_history(
        db_session,
        user_id=777,
        chrstn_mno="REPO-HIST-001",
    )
    latest_snapshot = (
        await recommendation_history_repo.get_latest_recommendation_history_with_score_snapshot(
            db_session,
            user_id=777,
            chrstn_mno="REPO-HIST-001",
        )
    )
    selected = await recommendation_history_repo.mark_recommendation_selected(
        db_session,
        rows[0],
    )
    selected_rows = await recommendation_history_repo.get_recommendation_histories(
        db_session,
        user_id=777,
        selected=True,
    )
    semantic_rows = await recommendation_history_repo.get_recommendation_histories(
        db_session,
        user_id=777,
        recommendation_type="SEMANTIC_AI",
    )

    assert latest.recommendation_score == Decimal("95.00")
    assert latest_snapshot.price_score == Decimal("90.00")
    assert selected.selected is True
    assert selected.selected_at is not None
    assert [row.recommendation_id for row in selected_rows] == [rows[0].recommendation_id]
    assert [row.recommendation_id for row in semantic_rows] == [rows[1].recommendation_id]


@pytest.mark.asyncio
async def test_charging_log_repo_filters_orders_and_paginates(db_session):
    await _create_station(db_session, "REPO-LOG-001")
    await _create_station(db_session, "REPO-LOG-002")
    created = await charging_log_repo.create_charging_logs(
        db_session,
        ChargingLogCreate(
            user_id=888,
            logs=[
                ChargingLogItemCreate(
                    chrstn_mno="REPO-LOG-001",
                    start_time=datetime(2026, 5, 24, 9, 0),
                    end_time=datetime(2026, 5, 24, 9, 30),
                    charged_amount=Decimal("1.10"),
                    charging_cost=Decimal("10000"),
                    waiting_time=3,
                ),
                ChargingLogItemCreate(
                    chrstn_mno="REPO-LOG-002",
                    start_time=datetime(2026, 5, 24, 10, 0),
                    end_time=datetime(2026, 5, 24, 10, 20),
                    charged_amount=Decimal("2.20"),
                    charging_cost=Decimal("21000"),
                    waiting_time=0,
                ),
            ],
        ),
    )

    all_logs = await charging_log_repo.get_charging_logs(db_session, user_id=888)
    station_logs = await charging_log_repo.get_charging_logs(
        db_session,
        user_id=888,
        chrstn_mno="REPO-LOG-001",
    )
    paged = await charging_log_repo.get_charging_logs(
        db_session,
        user_id=888,
        limit=1,
        offset=1,
    )

    assert [log.charging_log_id for log in all_logs] == [
        created[1].charging_log_id,
        created[0].charging_log_id,
    ]
    assert [log.chrstn_mno for log in station_logs] == ["REPO-LOG-001"]
    assert [log.charging_log_id for log in paged] == [created[0].charging_log_id]


@pytest.mark.asyncio
async def test_charging_log_repo_gets_recent_logs_for_recommendation_stats(
    db_session,
):
    await _create_station(db_session, "REPO-RECENT-LOG-001")
    await _create_station(db_session, "REPO-RECENT-LOG-002")
    await _create_station(db_session, "REPO-RECENT-LOG-OUT")
    created = await charging_log_repo.create_charging_logs(
        db_session,
        ChargingLogCreate(
            user_id=889,
            logs=[
                ChargingLogItemCreate(
                    chrstn_mno="REPO-RECENT-LOG-001",
                    start_time=datetime(2026, 5, 24, 9, 0),
                    end_time=datetime(2026, 5, 24, 9, 10),
                ),
                ChargingLogItemCreate(
                    chrstn_mno="REPO-RECENT-LOG-002",
                    start_time=datetime(2026, 5, 24, 10, 0),
                    end_time=datetime(2026, 5, 24, 10, 10),
                ),
                ChargingLogItemCreate(
                    chrstn_mno="REPO-RECENT-LOG-OUT",
                    start_time=datetime(2026, 5, 24, 11, 0),
                    end_time=datetime(2026, 5, 24, 11, 10),
                ),
            ],
        ),
    )

    logs = await charging_log_repo.get_recent_charging_logs_for_stations(
        db_session,
        ["REPO-RECENT-LOG-001", "REPO-RECENT-LOG-002"],
        limit=1,
    )
    empty = await charging_log_repo.get_recent_charging_logs_for_stations(
        db_session,
        [],
    )

    assert [log.charging_log_id for log in logs] == [created[1].charging_log_id]
    assert logs[0].chrstn_mno == "REPO-RECENT-LOG-002"
    assert empty == []
