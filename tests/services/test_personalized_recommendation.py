import pytest
from datetime import datetime, timedelta
from decimal import Decimal

from app.models.user import User
from app.schemas.charging_log_schema import ChargingLogCreate, ChargingLogItemCreate
from app.schemas.hydrogen_station_schema import HydrogenStationCreate
from app.schemas.hydrogen_station_status_schema import HydrogenStationStatusCreate
from app.schemas.user_preference_schema import (
    UserCreate,
    UserPreferenceLearningRequest,
    UserPreferenceUpdate,
)
from app.schemas.recommendation_history_schema import (
    RecommendationHistoryCreate,
    RecommendationStationCreate,
)
from app.schemas.recommendation_schema import RecommendationSearchRequest
from app.services.charging_log_service import ChargingLogService
from app.services.hydrogen_station_service import HydrogenStationService
from app.services.hydrogen_station_status_service import HydrogenStationStatusService
from app.services.recommendation_history_service import RecommendationHistoryService
from app.services.user_preference_service import UserPreferenceService
from app.services.recommendation_service import RecommendationService
from app.services.recommendation_service import haversine_distance


@pytest.mark.asyncio
async def test_create_user_initializes_default_preferences(db_session):
    user = await UserPreferenceService(db_session).create_user(
        UserCreate(
            name="신규사용자",
            phone="010-1111-2222",
            email="new-user@example.com",
        )
    )

    assert user.user_id is not None
    assert user.name == "신규사용자"
    assert user.preferences is not None
    assert user.preferences.weight_price == Decimal("1.0")


@pytest.mark.asyncio
async def test_create_user_rejects_duplicate_email(db_session):
    service = UserPreferenceService(db_session)
    payload = UserCreate(
        name="중복사용자",
        phone="010-1111-2222",
        email="duplicate@example.com",
    )

    await service.create_user(payload)

    with pytest.raises(Exception) as exc_info:
        await service.create_user(payload)

    assert getattr(exc_info.value, "status_code", None) == 409


@pytest.mark.asyncio
async def test_personalized_recommendation_and_preferences(db_session, monkeypatch):
    async def use_only_test_stations(self, _nl_query):
        return ["TEST-ST-001", "TEST-ST-002"]

    monkeypatch.setattr(
        "app.services.recommendation_candidate_filter_service."
        "RecommendationCandidateFilterService.filter_by_natural_language",
        use_only_test_stations,
    )

    # 1. Create a dummy user in database
    user = User(
        user_id=99,
        name="테스트맨",
        phone="010-9999-9999",
        email="testman@example.com",
    )
    db_session.add(user)
    await db_session.commit()

    # 2. Test UserPreference lazy-init and retrieve
    pref_service = UserPreferenceService(db_session)
    pref = await pref_service.get_user_preferences(99)
    assert pref.user_id == 99
    assert pref.weight_price == Decimal("1.0")  # default weight

    # 3. Test updating user preferences
    await pref_service.update_user_preferences(
        99,
        UserPreferenceUpdate(
            weight_price=Decimal("2.5"),
            weight_waiting_time=Decimal("1.5"),
            weight_distance=Decimal("0.5"),
            weight_facilities=Decimal("0.0"),
            safety_margin=Decimal("1.1"),
        )
    )
    updated_pref = await pref_service.get_user_preferences(99)
    assert updated_pref.weight_price == Decimal("2.5")
    assert updated_pref.weight_distance == Decimal("0.5")

    # 4. Create dummy stations for spatial and price filtering
    station_service = HydrogenStationService(db_session)
    
    # Station 1: Near current location, cheap
    await station_service.create_hydrogen_station(
        HydrogenStationCreate(
            chrstn_mno="TEST-ST-001",
            chrstn_nm="가까운 싼 충전소",
            ntsl_pc=9500,
            let=Decimal("37.4100"),
            lon=Decimal("126.7000"),
            oper_yn="Y",
        )
    )
    
    # Station 2: Detour route, expensive
    await station_service.create_hydrogen_station(
        HydrogenStationCreate(
            chrstn_mno="TEST-ST-002",
            chrstn_nm="먼 비싼 충전소",
            ntsl_pc=11000,
            let=Decimal("37.4500"),
            lon=Decimal("126.5000"),
            oper_yn="Y",
        )
    )

    # 5. Run personalized recommendation search
    # Current: 37.4050, 126.7210 (Incheon City Hall)
    # Destination: 37.4600, 126.4500 (Incheon Airport)
    # Remaining driving range: 45km, buffer: 15km
    rec_service = RecommendationService(db_session)
    request = RecommendationSearchRequest(
        user_id=99,
        current_latitude=Decimal("37.4050"),
        current_longitude=Decimal("126.7210"),
        destination_latitude=Decimal("37.4600"),
        destination_longitude=Decimal("126.4500"),
        remaining_range=Decimal("45.0"),
        nl_query="테스트 충전소만",
    )
    
    recommendations = await rec_service.get_personalized_recommendations(request)
    
    # Check that stations within the bounding circle are fetched
    assert len(recommendations) > 0
    
    # The cheaper, closer station (TEST-ST-001) should rank higher
    assert recommendations[0].chrstn_mno == "TEST-ST-001"
    assert recommendations[0].final_score > 0.0
    assert recommendations[0].is_reachable is True
    assert recommendations[0].delivery_payload.chrstn_mno == "TEST-ST-001"
    assert recommendations[0].delivery_payload.chrstn_nm == recommendations[0].chrstn_nm
    assert recommendations[0].delivery_payload.distance_to_station == recommendations[0].distance_to_station
    assert recommendations[0].delivery_payload.detour_distance == recommendations[0].detour_distance
    assert recommendations[0].delivery_payload.final_score == recommendations[0].final_score


@pytest.mark.asyncio
async def test_learn_from_selected_recommendation_moves_weights_gradually(db_session):
    service = UserPreferenceService(db_session)
    user = await service.create_user(
        UserCreate(
            name="학습사용자",
            phone="010-7777-8888",
            email="learning-user@example.com",
        )
    )
    await HydrogenStationService(db_session).create_hydrogen_station(
        HydrogenStationCreate(
            chrstn_mno="LEARN-SVC-ST-001",
            chrstn_nm="학습용 충전소",
        )
    )
    await RecommendationHistoryService(db_session).create_recommendation_histories(
        RecommendationHistoryCreate(
            user_id=user.user_id,
            recommendations=[
                RecommendationStationCreate(
                    chrstn_mno="LEARN-SVC-ST-001",
                    recommendation_score=Decimal("80.0"),
                    price_score=Decimal("40"),
                    waiting_time_score=Decimal("90"),
                    distance_score=Decimal("85"),
                    facilities_score=Decimal("25"),
                )
            ],
        )
    )

    updated_pref = await service.learn_from_selected_recommendation(
        user.user_id,
        UserPreferenceLearningRequest(
            chrstn_mno="LEARN-SVC-ST-001",
        ),
    )

    assert updated_pref.weight_price == Decimal("0.97")
    assert updated_pref.weight_waiting_time == Decimal("1.05")
    assert updated_pref.weight_distance == Decimal("1.04")
    assert updated_pref.weight_facilities == Decimal("0.94")


@pytest.mark.asyncio
async def test_learning_requires_server_side_score_snapshot(db_session):
    service = UserPreferenceService(db_session)
    user = await service.create_user(
        UserCreate(
            name="점수없는학습사용자",
            phone="010-7777-9999",
            email="missing-score-learning-user@example.com",
        )
    )
    await HydrogenStationService(db_session).create_hydrogen_station(
        HydrogenStationCreate(
            chrstn_mno="LEARN-SVC-ST-002",
            chrstn_nm="점수 없는 추천 이력 충전소",
        )
    )
    await RecommendationHistoryService(db_session).create_recommendation_histories(
        RecommendationHistoryCreate(
            user_id=user.user_id,
            recommendations=[
                RecommendationStationCreate(
                    chrstn_mno="LEARN-SVC-ST-002",
                    recommendation_score=Decimal("80.0"),
                )
            ],
        )
    )

    with pytest.raises(Exception) as exc_info:
        await service.learn_from_selected_recommendation(
            user.user_id,
            UserPreferenceLearningRequest(
                chrstn_mno="LEARN-SVC-ST-002",
            ),
        )

    assert getattr(exc_info.value, "status_code", None) == 409

    histories = await RecommendationHistoryService(
        db_session
    ).get_recommendation_histories(
        user_id=user.user_id,
        chrstn_mno="LEARN-SVC-ST-002",
    )
    assert histories[0].selected is False


def test_haversine_distance_returns_zero_for_same_coordinate():
    assert haversine_distance(37.405, 126.721, 37.405, 126.721) == 0


def test_haversine_distance_matches_known_short_route_distance():
    distance = haversine_distance(37.405, 126.721, 37.460, 126.450)

    assert round(distance, 1) == 24.7


@pytest.mark.asyncio
async def test_personalized_recommendation_scores_low_detour_route_higher(
    db_session,
    monkeypatch,
):
    async def use_detour_scenario_stations(self, _nl_query):
        return ["DETOUR-LOW-001", "DETOUR-HIGH-001"]

    monkeypatch.setattr(
        "app.services.recommendation_candidate_filter_service."
        "RecommendationCandidateFilterService.filter_by_natural_language",
        use_detour_scenario_stations,
    )
    user = await UserPreferenceService(db_session).create_user(
        UserCreate(
            name="우회거리 시나리오 사용자",
            phone="010-7777-0101",
            email="detour-scenario-user@example.com",
        )
    )
    await UserPreferenceService(db_session).update_user_preferences(
        user.user_id,
        UserPreferenceUpdate(
            weight_price=Decimal("0.0"),
            weight_waiting_time=Decimal("0.0"),
            weight_distance=Decimal("3.0"),
            weight_facilities=Decimal("0.0"),
            safety_margin=Decimal("1.0"),
        ),
    )

    station_service = HydrogenStationService(db_session)
    await station_service.create_hydrogen_station(
        HydrogenStationCreate(
            chrstn_mno="DETOUR-LOW-001",
            chrstn_nm="목적지 방향 저우회 충전소",
            ntsl_pc=10000,
            let=Decimal("37.0000"),
            lon=Decimal("127.1000"),
            oper_yn="Y",
        )
    )
    await station_service.create_hydrogen_station(
        HydrogenStationCreate(
            chrstn_mno="DETOUR-HIGH-001",
            chrstn_nm="가까워 보이는 고우회 충전소",
            ntsl_pc=10000,
            let=Decimal("37.0900"),
            lon=Decimal("127.0000"),
            oper_yn="Y",
        )
    )

    recommendations = await RecommendationService(
        db_session
    ).get_personalized_recommendations(
        RecommendationSearchRequest(
            user_id=user.user_id,
            current_latitude=Decimal("37.0000"),
            current_longitude=Decimal("127.0000"),
            destination_latitude=Decimal("37.0000"),
            destination_longitude=Decimal("127.2000"),
            remaining_range=Decimal("100.0"),
            nl_query="우회거리 테스트 충전소만",
        )
    )

    assert [rec.chrstn_mno for rec in recommendations] == [
        "DETOUR-LOW-001",
        "DETOUR-HIGH-001",
    ]
    low_detour, high_detour = recommendations
    assert low_detour.detour_distance == pytest.approx(0.0, abs=0.1)
    assert high_detour.detour_distance > 10.0
    assert low_detour.sub_scores.distance > 95.0
    assert high_detour.sub_scores.distance < 30.0
    assert low_detour.final_score > high_detour.final_score
    assert low_detour.delivery_payload.detour_distance == low_detour.detour_distance


@pytest.mark.asyncio
async def test_personalized_recommendation_uses_path_range_candidates(
    db_session,
    monkeypatch,
):
    async def use_only_path_range_test_stations(self, _nl_query):
        return [
            "REC-PATH-RANGE-IN",
            "REC-PATH-RANGE-INNER",
            "REC-PATH-RANGE-OUT",
        ]

    monkeypatch.setattr(
        "app.services.recommendation_candidate_filter_service."
        "RecommendationCandidateFilterService.filter_by_natural_language",
        use_only_path_range_test_stations,
    )
    user = await UserPreferenceService(db_session).create_user(
        UserCreate(
            name="실경로 후보 추천 사용자",
            phone="010-7777-0102",
            email="path-range-recommendation-user@example.com",
        )
    )
    station_service = HydrogenStationService(db_session)
    for station in [
        HydrogenStationCreate(
            chrstn_mno="REC-PATH-RANGE-IN",
            chrstn_nm="추천 경로 범위 포함 충전소",
            let=Decimal("36.0200"),
            lon=Decimal("128.1000"),
            oper_yn="Y",
        ),
        HydrogenStationCreate(
            chrstn_mno="REC-PATH-RANGE-INNER",
            chrstn_nm="추천 경로 내부 제외 충전소",
            let=Decimal("36.1000"),
            lon=Decimal("128.1000"),
            oper_yn="Y",
        ),
        HydrogenStationCreate(
            chrstn_mno="REC-PATH-RANGE-OUT",
            chrstn_nm="추천 경로 범위 외부 충전소",
            let=Decimal("36.5000"),
            lon=Decimal("128.5000"),
            oper_yn="Y",
        ),
    ]:
        await station_service.create_hydrogen_station(station)

    recommendations = await RecommendationService(
        db_session
    ).get_personalized_recommendations(
        RecommendationSearchRequest(
            user_id=user.user_id,
            current_latitude=Decimal("36.0"),
            current_longitude=Decimal("128.0"),
            destination_latitude=Decimal("36.2"),
            destination_longitude=Decimal("128.2"),
            remaining_range=Decimal("100.0"),
        )
    )

    assert {rec.chrstn_mno for rec in recommendations} == {
        "REC-PATH-RANGE-IN",
        "REC-PATH-RANGE-INNER",
    }


@pytest.mark.asyncio
async def test_personalized_recommendation_uses_queue_time_history(
    db_session,
    monkeypatch,
):
    async def use_queue_history_test_stations(self, _nl_query):
        return ["QUEUE-HISTORY-FAST", "QUEUE-HISTORY-SLOW"]

    monkeypatch.setattr(
        "app.services.recommendation_candidate_filter_service."
        "RecommendationCandidateFilterService.filter_by_natural_language",
        use_queue_history_test_stations,
    )
    user = await UserPreferenceService(db_session).create_user(
        UserCreate(
            name="대기시간 히스토리 사용자",
            phone="010-7777-0103",
            email="queue-history-recommendation-user@example.com",
        )
    )
    await UserPreferenceService(db_session).update_user_preferences(
        user.user_id,
        UserPreferenceUpdate(
            weight_price=Decimal("0.0"),
            weight_waiting_time=Decimal("3.0"),
            weight_distance=Decimal("0.0"),
            weight_facilities=Decimal("0.0"),
            safety_margin=Decimal("1.0"),
        ),
    )

    station_service = HydrogenStationService(db_session)
    for station_id, name in [
        ("QUEUE-HISTORY-FAST", "히스토리상 빠른 충전소"),
        ("QUEUE-HISTORY-SLOW", "히스토리상 느린 충전소"),
    ]:
        await station_service.create_hydrogen_station(
            HydrogenStationCreate(
                chrstn_mno=station_id,
                chrstn_nm=name,
                ntsl_pc=10000,
                let=Decimal("37.0000"),
                lon=Decimal("127.1000"),
                oper_yn="Y",
            )
        )
        await HydrogenStationStatusService(db_session).create_hydrogen_station_status(
            HydrogenStationStatusCreate(
                chrstn_mno=station_id,
                wait_vhcle_alge=0,
                tt_pressr=700,
                prfect_elctc_posbl_alge=10,
                oper_sttus_nm="운영중",
                pos_sttus_nm="영업중",
            )
        )

    base_time = datetime(2026, 5, 24, 0, 0)
    fast_logs = []
    slow_logs = []
    for hour in range(24):
        started_at = base_time + timedelta(hours=hour)
        fast_logs.append(
            ChargingLogItemCreate(
                chrstn_mno="QUEUE-HISTORY-FAST",
                start_time=started_at,
                end_time=started_at + timedelta(minutes=6),
                waiting_time=0,
            )
        )
        slow_logs.append(
            ChargingLogItemCreate(
                chrstn_mno="QUEUE-HISTORY-SLOW",
                start_time=started_at,
                end_time=started_at + timedelta(minutes=20),
                waiting_time=30,
            )
        )

    await ChargingLogService(db_session).create_charging_logs(
        ChargingLogCreate(
            user_id=user.user_id,
            logs=fast_logs + slow_logs,
        )
    )

    recommendations = await RecommendationService(
        db_session
    ).get_personalized_recommendations(
        RecommendationSearchRequest(
            user_id=user.user_id,
            current_latitude=Decimal("37.0000"),
            current_longitude=Decimal("127.0000"),
            destination_latitude=Decimal("37.0000"),
            destination_longitude=Decimal("127.2000"),
            remaining_range=Decimal("100.0"),
            nl_query="대기시간 히스토리 테스트 충전소만",
        )
    )

    assert [rec.chrstn_mno for rec in recommendations] == [
        "QUEUE-HISTORY-FAST",
        "QUEUE-HISTORY-SLOW",
    ]
    assert recommendations[0].wait_time_minutes < recommendations[1].wait_time_minutes
    assert recommendations[0].sub_scores.waiting_time > recommendations[1].sub_scores.waiting_time


@pytest.mark.asyncio
async def test_personalized_recommendation_penalizes_unavailable_queue_status(
    db_session,
    monkeypatch,
):
    async def use_status_penalty_test_stations(self, _nl_query):
        return ["QUEUE-STATUS-OPEN", "QUEUE-STATUS-CLOSED"]

    monkeypatch.setattr(
        "app.services.recommendation_candidate_filter_service."
        "RecommendationCandidateFilterService.filter_by_natural_language",
        use_status_penalty_test_stations,
    )
    user = await UserPreferenceService(db_session).create_user(
        UserCreate(
            name="운영상태 패널티 사용자",
            phone="010-7777-0104",
            email="queue-status-penalty-user@example.com",
        )
    )
    await UserPreferenceService(db_session).update_user_preferences(
        user.user_id,
        UserPreferenceUpdate(
            weight_price=Decimal("0.0"),
            weight_waiting_time=Decimal("3.0"),
            weight_distance=Decimal("0.0"),
            weight_facilities=Decimal("0.0"),
            safety_margin=Decimal("1.0"),
        ),
    )

    station_service = HydrogenStationService(db_session)
    for station_id in ["QUEUE-STATUS-OPEN", "QUEUE-STATUS-CLOSED"]:
        await station_service.create_hydrogen_station(
            HydrogenStationCreate(
                chrstn_mno=station_id,
                chrstn_nm=f"{station_id} 충전소",
                ntsl_pc=10000,
                let=Decimal("37.0000"),
                lon=Decimal("127.1000"),
                oper_yn="Y",
            )
        )

    status_service = HydrogenStationStatusService(db_session)
    await status_service.create_hydrogen_station_status(
        HydrogenStationStatusCreate(
            chrstn_mno="QUEUE-STATUS-OPEN",
            wait_vhcle_alge=3,
            tt_pressr=700,
            prfect_elctc_posbl_alge=10,
            oper_sttus_nm="운영중",
            pos_sttus_nm="영업중",
        )
    )
    await status_service.create_hydrogen_station_status(
        HydrogenStationStatusCreate(
            chrstn_mno="QUEUE-STATUS-CLOSED",
            wait_vhcle_alge=0,
            tt_pressr=0,
            prfect_elctc_posbl_alge=0,
            oper_sttus_nm="영업마감",
            pos_sttus_nm="점검중",
        )
    )

    recommendations = await RecommendationService(
        db_session
    ).get_personalized_recommendations(
        RecommendationSearchRequest(
            user_id=user.user_id,
            current_latitude=Decimal("37.0000"),
            current_longitude=Decimal("127.0000"),
            destination_latitude=Decimal("37.0000"),
            destination_longitude=Decimal("127.2000"),
            remaining_range=Decimal("100.0"),
            nl_query="운영상태 패널티 테스트 충전소만",
        )
    )

    assert [rec.chrstn_mno for rec in recommendations] == [
        "QUEUE-STATUS-OPEN",
        "QUEUE-STATUS-CLOSED",
    ]
    closed = recommendations[1]
    assert closed.wait_time_minutes == 180
    assert closed.sub_scores.waiting_time == 0.0
    assert closed.final_score < recommendations[0].final_score
    assert "운영/압력 상태" in closed.recommendation_reason


@pytest.mark.asyncio
async def test_personalized_recommendation_uses_latest_status_snapshot(
    db_session,
    monkeypatch,
):
    async def use_latest_status_test_station(self, _nl_query):
        return ["QUEUE-LATEST-STATUS"]

    monkeypatch.setattr(
        "app.services.recommendation_candidate_filter_service."
        "RecommendationCandidateFilterService.filter_by_natural_language",
        use_latest_status_test_station,
    )
    user = await UserPreferenceService(db_session).create_user(
        UserCreate(
            name="최신상태 사용자",
            phone="010-7777-0105",
            email="queue-latest-status-user@example.com",
        )
    )
    await HydrogenStationService(db_session).create_hydrogen_station(
        HydrogenStationCreate(
            chrstn_mno="QUEUE-LATEST-STATUS",
            chrstn_nm="최신 상태 반영 충전소",
            let=Decimal("37.0000"),
            lon=Decimal("127.1000"),
            oper_yn="Y",
        )
    )
    status_service = HydrogenStationStatusService(db_session)
    await status_service.create_hydrogen_station_status(
        HydrogenStationStatusCreate(
            chrstn_mno="QUEUE-LATEST-STATUS",
            wait_vhcle_alge=9,
            last_mdfcn_dt="20260524090000",
        )
    )
    await status_service.create_hydrogen_station_status(
        HydrogenStationStatusCreate(
            chrstn_mno="QUEUE-LATEST-STATUS",
            wait_vhcle_alge=1,
            last_mdfcn_dt="20260524100000",
        )
    )

    recommendations = await RecommendationService(
        db_session
    ).get_personalized_recommendations(
        RecommendationSearchRequest(
            user_id=user.user_id,
            current_latitude=Decimal("37.0000"),
            current_longitude=Decimal("127.0000"),
            destination_latitude=Decimal("37.0000"),
            destination_longitude=Decimal("127.2000"),
            remaining_range=Decimal("100.0"),
            nl_query="최신 상태 테스트 충전소만",
        )
    )

    assert len(recommendations) == 1
    assert recommendations[0].wait_vehicles == 1


@pytest.mark.asyncio
async def test_personalized_recommendation_returns_empty_when_no_active_stations(
    db_session,
    monkeypatch,
):
    async def use_missing_station_id(self, _nl_query):
        return ["TEST-ST-NOT-EXISTS"]

    monkeypatch.setattr(
        "app.services.recommendation_candidate_filter_service."
        "RecommendationCandidateFilterService.filter_by_natural_language",
        use_missing_station_id,
    )
    user = await UserPreferenceService(db_session).create_user(
        UserCreate(
            name="추천 빈 결과 사용자",
            phone="010-7777-0001",
            email="empty-recommendation-user@example.com",
        )
    )

    recommendations = await RecommendationService(
        db_session
    ).get_personalized_recommendations(
        RecommendationSearchRequest(
            user_id=user.user_id,
            current_latitude=Decimal("37.4050"),
            current_longitude=Decimal("126.7210"),
            destination_latitude=Decimal("37.4600"),
            destination_longitude=Decimal("126.4500"),
            remaining_range=Decimal("45.0"),
            nl_query="없는 충전소만",
        )
    )

    assert recommendations == []


@pytest.mark.asyncio
async def test_personalized_recommendation_penalizes_unreachable_station(
    db_session,
    monkeypatch,
):
    async def use_unreachable_test_station(self, _nl_query):
        return ["TEST-ST-UNREACHABLE"]

    monkeypatch.setattr(
        "app.services.recommendation_candidate_filter_service."
        "RecommendationCandidateFilterService.filter_by_natural_language",
        use_unreachable_test_station,
    )
    user = await UserPreferenceService(db_session).create_user(
        UserCreate(
            name="도달 불가 추천 사용자",
            phone="010-7777-0002",
            email="unreachable-recommendation-user@example.com",
        )
    )
    await HydrogenStationService(db_session).create_hydrogen_station(
        HydrogenStationCreate(
            chrstn_mno="TEST-ST-UNREACHABLE",
            chrstn_nm="도달 불가 충전소",
            ntsl_pc=9500,
            let=Decimal("37.4100"),
            lon=Decimal("126.7000"),
            oper_yn="Y",
        )
    )

    recommendations = await RecommendationService(
        db_session
    ).get_personalized_recommendations(
        RecommendationSearchRequest(
            user_id=user.user_id,
            current_latitude=Decimal("37.4050"),
            current_longitude=Decimal("126.7210"),
            destination_latitude=Decimal("37.4600"),
            destination_longitude=Decimal("126.4500"),
            remaining_range=Decimal("1.0"),
        )
    )

    assert len(recommendations) == 1
    assert recommendations[0].is_reachable is False
    assert recommendations[0].final_score < 10
    assert "초과" in recommendations[0].recommendation_reason


@pytest.mark.asyncio
async def test_learning_uses_client_score_fallback_when_history_has_no_snapshot(
    db_session,
):
    service = UserPreferenceService(db_session)
    user = await service.create_user(
        UserCreate(
            name="클라이언트 점수 학습 사용자",
            phone="010-7777-0003",
            email="client-score-learning-user@example.com",
        )
    )
    await HydrogenStationService(db_session).create_hydrogen_station(
        HydrogenStationCreate(
            chrstn_mno="LEARN-SVC-ST-CLIENT",
            chrstn_nm="클라이언트 점수 충전소",
        )
    )
    await RecommendationHistoryService(db_session).create_recommendation_histories(
        RecommendationHistoryCreate(
            user_id=user.user_id,
            recommendations=[
                RecommendationStationCreate(
                    chrstn_mno="LEARN-SVC-ST-CLIENT",
                    recommendation_score=Decimal("80.0"),
                )
            ],
        )
    )

    updated_pref = await service.learn_from_selected_recommendation(
        user.user_id,
        UserPreferenceLearningRequest(
            chrstn_mno="LEARN-SVC-ST-CLIENT",
            price_score=Decimal("100"),
            waiting_time_score=Decimal("0"),
            distance_score=Decimal("0"),
            facilities_score=Decimal("0"),
        ),
    )

    assert updated_pref.weight_price == Decimal("1.30")
    assert updated_pref.weight_waiting_time == Decimal("0.90")
    assert updated_pref.weight_distance == Decimal("0.90")
    assert updated_pref.weight_facilities == Decimal("0.90")


@pytest.mark.asyncio
async def test_learning_rejects_partial_client_score_fallback(db_session):
    service = UserPreferenceService(db_session)
    user = await service.create_user(
        UserCreate(
            name="부분 점수 학습 사용자",
            phone="010-7777-0004",
            email="partial-score-learning-user@example.com",
        )
    )
    await HydrogenStationService(db_session).create_hydrogen_station(
        HydrogenStationCreate(
            chrstn_mno="LEARN-SVC-ST-PARTIAL",
            chrstn_nm="부분 점수 충전소",
        )
    )
    await RecommendationHistoryService(db_session).create_recommendation_histories(
        RecommendationHistoryCreate(
            user_id=user.user_id,
            recommendations=[
                RecommendationStationCreate(
                    chrstn_mno="LEARN-SVC-ST-PARTIAL",
                    recommendation_score=Decimal("80.0"),
                )
            ],
        )
    )

    with pytest.raises(Exception) as exc_info:
        await service.learn_from_selected_recommendation(
            user.user_id,
            UserPreferenceLearningRequest(
                chrstn_mno="LEARN-SVC-ST-PARTIAL",
                price_score=Decimal("100"),
            ),
        )

    assert getattr(exc_info.value, "status_code", None) == 422
