import pytest
from decimal import Decimal

from app.models.user import User
from app.schemas.hydrogen_stations_schemas import HydrogenStationCreate
from app.schemas.user_preference_schemas import UserPreferenceUpdate
from app.schemas.recommendation_request_schemas import RecommendationSearchRequest
from app.services.hydrogen_station_service import HydrogenStationService
from app.services.user_preference_service import UserPreferenceService
from app.services.recommendation_service import RecommendationService
from app.api.navigation_api import PushWaypointRequest, push_waypoint


@pytest.mark.asyncio
async def test_personalized_recommendation_and_preferences(db_session):
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
        alpha=Decimal("15.0"),
    )
    
    recommendations = await rec_service.get_personalized_recommendations(request)
    
    # Check that stations within the bounding circle are fetched
    assert len(recommendations) > 0
    
    # The cheaper, closer station (TEST-ST-001) should rank higher
    assert recommendations[0].chrstn_mno == "TEST-ST-001"
    assert recommendations[0].final_score > 0.0
    assert recommendations[0].is_reachable is True
