import math
import os
import logging
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.models.hydrogen_stations import HydrogenStation
from app.models.recommendation_history import RecommendationHistory
from app.repositories import user_preference_repo, recommendation_history_repo
from app.schemas.recommendation_request_schemas import (
    RecommendationSearchRequest,
    RecommendedStationResponse,
    SubScores,
)
from app.schemas.recommendation_history_schema import (
    RecommendationHistoryCreate,
    RecommendationStationCreate,
)
from app.services.text_to_sql_service import TextToSqlService

logger = logging.getLogger("recommendation_service")


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Computes the geodesic distance in kilometers between two coordinates using the Haversine formula.
    """
    R = 6371.0  # Earth's radius in kilometers
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (math.sin(d_lat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


class RecommendationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.text_to_sql_service = TextToSqlService(db)

    async def get_personalized_recommendations(
        self,
        request: RecommendationSearchRequest,
    ) -> list[RecommendedStationResponse]:
        # 1. Fetch user preference weights
        pref = await user_preference_repo.get_user_preferences(self.db, request.user_id)
        if pref is None:
            # If user does not exist, raise exception
            raise HTTPException(
                status_code=404,
                detail=f"User with ID {request.user_id} not found in database.",
            )

        w_price = float(pref.weight_price)
        w_wait = float(pref.weight_waiting_time)
        w_distance = float(pref.weight_distance)
        w_facilities = float(pref.weight_facilities)
        safety_margin = float(pref.safety_margin)

        # 2. Step 1: Text-to-SQL Semantic Filter
        filtered_mno_list = None
        if request.nl_query and request.nl_query.strip():
            logger.info(f"Running Text-to-SQL for query: '{request.nl_query}'")
            filtered_mno_list = await self.text_to_sql_service.execute_semantic_search(request.nl_query)
            if filtered_mno_list is not None:
                logger.info(f"Text-to-SQL matched {len(filtered_mno_list)} stations.")
                if not filtered_mno_list:
                    # Semantic search yielded zero results, return early empty list
                    return []
            else:
                logger.warning("Text-to-SQL returned None (possibly missing Gemini key). Falling back to global list.")

        # 3. Query all stations from DB with status and facilities relationships
        stmt = (
            select(HydrogenStation)
            .where(HydrogenStation.oper_yn == "Y")
            .where(HydrogenStation.del_at == "0")
            .options(
                selectinload(HydrogenStation.status_list),
                selectinload(HydrogenStation.facilities_list),
            )
        )
        
        # Apply Text-to-SQL filter if it succeeded
        if filtered_mno_list is not None:
            stmt = stmt.where(HydrogenStation.chrstn_mno.in_(filtered_mno_list))

        result = await self.db.execute(stmt)
        stations = result.scalars().all()

        if not stations:
            return []

        # 4. Calculate direct distance from current location to destination
        cur_lat = float(request.current_latitude)
        cur_lon = float(request.current_longitude)
        dest_lat = float(request.destination_latitude)
        dest_lon = float(request.destination_longitude)
        
        direct_dist = haversine_distance(cur_lat, cur_lon, dest_lat, dest_lon)
        search_radius = direct_dist + float(request.alpha)

        # 5. Pre-calculate spatial bounds & collect price stats
        candidate_stations = []
        prices = []

        for st in stations:
            st_lat = float(st.let) if st.let else 0.0
            st_lon = float(st.lon) if st.lon else 0.0
            
            # Distance from current location to this station
            dist_to_station = haversine_distance(cur_lat, cur_lon, st_lat, st_lon)
            
            # Bounding circle filtering
            if dist_to_station > search_radius:
                continue

            # Distance from station to destination
            dist_to_dest = haversine_distance(st_lat, st_lon, dest_lat, dest_lon)
            
            # Detour distance
            detour_dist = max(0.0, dist_to_station + dist_to_dest - direct_dist)

            candidate_stations.append({
                "model": st,
                "lat": st_lat,
                "lon": st_lon,
                "dist_to_station": dist_to_station,
                "dist_to_dest": dist_to_dest,
                "detour_distance": detour_dist,
            })

            if st.ntsl_pc:
                prices.append(st.ntsl_pc)

        if not candidate_stations:
            return []

        # Find pricing bounds for normalization
        min_price = min(prices) if prices else 9000.0
        max_price = max(prices) if prices else 11000.0
        price_range = max_price - min_price

        # 6. Score each candidate
        scored_candidates = []
        for cand in candidate_stations:
            st = cand["model"]
            dist_to_st = cand["dist_to_station"]
            detour = cand["detour_distance"]

            # Reachability Check
            rem_range = float(request.remaining_range)
            is_reachable = (dist_to_st * safety_margin) <= rem_range

            # Price Score: cheaper is better
            price_val = st.ntsl_pc if st.ntsl_pc else min_price
            if price_range > 0:
                price_score = 100.0 * (max_price - price_val) / price_range
            else:
                price_score = 100.0

            # Waiting Time Score: fewer waiting cars is better
            latest_status = st.status_list[0] if st.status_list else None
            wait_cars = latest_status.wait_vhcle_alge if latest_status and latest_status.wait_vhcle_alge else 0
            # Exponential decay: 0 cars -> 100, 3 cars -> 36.8, etc.
            wait_score = 100.0 * math.exp(-wait_cars / 3.0)

            # Distance Score: smaller detour is better
            # Exponential decay: 0km detour -> 100, 8km detour -> 36.8, etc.
            dist_score = 100.0 * math.exp(-detour / 8.0)

            # Facilities Score: more additional services is better
            active_facilities = [
                f.adi_info_se_nm for f in st.facilities_list 
                if f.del_at == "0" and f.adi_info_se_nm
            ]
            fac_count = len(active_facilities)
            fac_score = min(100.0, fac_count * 25.0)

            # Compute Weighted Score
            total_weight = w_price + w_wait + w_distance + w_facilities
            if total_weight > 0:
                final_score = (
                    (w_price * price_score) +
                    (w_wait * wait_score) +
                    (w_distance * dist_score) +
                    (w_facilities * fac_score)
                ) / total_weight
            else:
                final_score = (price_score + wait_score + dist_score + fac_score) / 4.0

            # Reduce score significantly if unreachable
            if not is_reachable:
                # Apply heavy penalty but keep in the list for visualization
                final_score *= 0.1

            # Generate natural language reason
            reasons = []
            if w_distance >= 1.5 and detour <= 2.0:
                reasons.append("우회 거리가 최소화된 최적 경로 상에 있습니다.")
            if w_price >= 1.5 and price_val <= min_price + 300:
                reasons.append("판매 가격이 저렴하여 경제적입니다.")
            if w_wait >= 1.5 and wait_cars <= 1:
                reasons.append("실시간 대기 차량이 적어 빠른 충전이 가능합니다.")
            if w_facilities >= 1.5 and fac_count >= 2:
                reasons.append(f"주변 편의시설({', '.join(active_facilities[:2])})이 잘 구비되어 있습니다.")

            if not reasons:
                if is_reachable:
                    reasons.append("사용자 가중치 분석 결과 전반적 매칭도가 매우 높습니다.")
                else:
                    reasons.append("현재 주행가능거리를 초과하여 경로 충전소로 도달이 불가능할 수 있습니다.")

            reason_str = " ".join(reasons)

            # Generate simulated Hyundai navigation deeplink
            deeplink = (
                f"hyundainav://route?dest_lat={dest_lat}&dest_lon={dest_lon}"
                f"&waypoint1_lat={cand['lat']}&waypoint1_lon={cand['lon']}"
                f"&waypoint1_name={st.chrstn_nm}&user_id={request.user_id}"
            )

            scored_candidates.append(
                RecommendedStationResponse(
                    chrstn_mno=st.chrstn_mno,
                    chrstn_nm=st.chrstn_nm,
                    road_nm_addr=st.road_nm_addr or st.lotno_addr,
                    ntsl_pc=st.ntsl_pc,
                    distance_to_station=round(dist_to_st, 2),
                    distance_to_destination=round(cand["dist_to_dest"], 2),
                    detour_distance=round(detour, 2),
                    wait_vehicles=wait_cars,
                    wait_time_minutes=wait_cars * 15,
                    facilities=active_facilities,
                    is_reachable=is_reachable,
                    sub_scores=SubScores(
                        price=round(price_score, 1),
                        waiting_time=round(wait_score, 1),
                        distance=round(dist_score, 1),
                        facilities=round(fac_score, 1),
                    ),
                    final_score=round(final_score, 1),
                    recommendation_reason=reason_str,
                    hyundai_nav_deeplink=deeplink,
                )
            )

        # 7. Sort by final score descending
        scored_candidates.sort(key=lambda x: x.final_score, reverse=True)

        # 8. Record the top recommendations in history for analytics (up to top 5)
        top_recs = scored_candidates[:5]
        if top_recs:
            history_payload = RecommendationHistoryCreate(
                user_id=request.user_id,
                user_latitude=Decimal(str(cur_lat)),
                user_longitude=Decimal(str(cur_lon)),
                vehicle_remaining_hydrogen=Decimal(str(request.remaining_range)),
                recommendations=[
                    RecommendationStationCreate(
                        chrstn_mno=r.chrstn_mno,
                        recommendation_score=Decimal(str(r.final_score)),
                        recommendation_reason=r.recommendation_reason[:250],
                        estimated_arrival_time=int(r.distance_to_station * 1.5),  # rough estimate: 1.5 mins per km
                        selected=False,
                        selected_at=None,
                        recommendation_type="PERSONALIZED" if not request.nl_query else "SEMANTIC_AI",
                    )
                    for r in top_recs
                ]
            )
            # Commit background recommendation logs asynchronously
            await recommendation_history_repo.create_recommendation_histories(self.db, history_payload)

        return scored_candidates
