import math
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import (
    charging_log_repo,
    hydrogen_station_repo,
    recommendation_history_repo,
)
from app.schemas.recommendation_schema import (
    RecommendationSearchRequest,
    RecommendedStationResponse,
    SubScores,
)
from app.schemas.recommendation_history_schema import (
    RecommendationHistoryCreate,
    RecommendationStationCreate,
)
from app.services.recommendation_candidate_filter_service import (
    RecommendationCandidateFilterService,
)
from app.services.recommendation_delivery_payload_service import (
    RecommendationDeliveryPayloadService,
)
from app.services.recommendation_reason_service import (
    RecommendationReasonService,
    RecommendationWeights,
    StationReasonFacts,
)
from app.services.path_range_specification import find_charging_stations
from app.services.queue_time_estimation_service import QueueTimeEstimationService
from app.services.user_preference_service import UserPreferenceService

logger = logging.getLogger("recommendation_service")

RECOMMENDATION_RESPONSE_LIMIT = 5
RECOMMENDATION_HISTORY_LOGS_PER_STATION = 20
AUTO_ALPHA_RATIO = 0.60
PATH_RANGE_ESTIMATED_ROUTE_RATIO = 1.60
PATH_RANGE_PADDING_KM = 5.0
ROUTE_MINUTES_PER_KM = 1.5
WAIT_SCORE_DECAY_MINUTES = 18.0


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
        self.candidate_filter_service = RecommendationCandidateFilterService(db)
        self.delivery_payload_service = RecommendationDeliveryPayloadService()
        self.queue_time_estimation_service = QueueTimeEstimationService()
        self.reason_service = RecommendationReasonService()

    async def get_personalized_recommendations(
        self,
        request: RecommendationSearchRequest,
    ) -> list[RecommendedStationResponse]:
        # 1. Fetch user preference weights
        pref = await UserPreferenceService(self.db).get_user_preferences(request.user_id)

        w_price = float(pref.weight_price)
        w_wait = float(pref.weight_waiting_time)
        w_distance = float(pref.weight_distance)
        w_facilities = float(pref.weight_facilities)
        safety_margin = float(pref.safety_margin)

        cur_lat = float(request.current_latitude)
        cur_lon = float(request.current_longitude)
        dest_lat = float(request.destination_latitude)
        dest_lon = float(request.destination_longitude)
        direct_dist = haversine_distance(cur_lat, cur_lon, dest_lat, dest_lon)

        # 2. Step 1: Optional rule-based natural-language candidate filter.
        filtered_mno_list = await self.candidate_filter_service.filter_by_natural_language(
            request.nl_query
        )
        if filtered_mno_list == []:
            return []

        use_path_range_filter = False
        try:
            estimated_route_distance = direct_dist * PATH_RANGE_ESTIMATED_ROUTE_RATIO
            path_range_result = await find_charging_stations(
                self.db,
                x_lat=cur_lat,
                x_lng=cur_lon,
                y_lat=dest_lat,
                y_lng=dest_lon,
                actual_distance_km=estimated_route_distance,
                padding_km=PATH_RANGE_PADDING_KM,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        path_range_mno_list = [
            station.chrstn_mno
            for station in path_range_result["candidate_stations"]
        ]
        if path_range_mno_list:
            if filtered_mno_list is None:
                filtered_mno_list = path_range_mno_list
                use_path_range_filter = True
            else:
                path_range_ids = set(path_range_mno_list)
                filtered_mno_list = [
                    chrstn_mno
                    for chrstn_mno in filtered_mno_list
                    if chrstn_mno in path_range_ids
                ]
                use_path_range_filter = True
                if not filtered_mno_list:
                    return []

        auto_alpha = 0.0 if use_path_range_filter else direct_dist * AUTO_ALPHA_RATIO
        search_radius = direct_dist + auto_alpha

        # 3. Query active stations with latest realtime status and facilities
        stations = await hydrogen_station_repo.get_active_hydrogen_stations_for_recommendation(
            self.db,
            filtered_mno_list,
        )

        if not stations:
            return []

        # 5. Pre-calculate spatial bounds & collect price stats
        candidate_stations = []
        prices = []

        for st in stations:
            st_lat = float(st.let) if st.let else 0.0
            st_lon = float(st.lon) if st.lon else 0.0
            
            # Distance from current location to this station
            dist_to_station = haversine_distance(cur_lat, cur_lon, st_lat, st_lon)
            
            # Bounding circle filtering. Path-range requests already narrowed
            # candidates using the actual route distance envelope.
            if not use_path_range_filter and dist_to_station > search_radius:
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
        station_ids = [cand["model"].chrstn_mno for cand in candidate_stations]
        recent_logs = await charging_log_repo.get_recent_charging_logs_for_stations(
            self.db,
            station_ids,
            limit=max(100, len(station_ids) * RECOMMENDATION_HISTORY_LOGS_PER_STATION),
        )
        queue_history_stats = self.queue_time_estimation_service.build_history_stats(
            recent_logs
        )

        # 6. Score each candidate
        weights = RecommendationWeights(
            price=w_price,
            wait=w_wait,
            distance=w_distance,
            facilities=w_facilities,
        )
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

            # Waiting Time Score: estimate actual queue time from realtime
            # status, station capacity hints, and station-level charging logs.
            latest_status = st.status_list[0] if st.status_list else None
            arrival_minutes = int(round(dist_to_st * ROUTE_MINUTES_PER_KM))
            arrival_time = datetime.now().astimezone(None) + timedelta(
                minutes=arrival_minutes
            )
            queue_estimate = self.queue_time_estimation_service.estimate(
                station=st,
                status=latest_status,
                history=queue_history_stats.get(st.chrstn_mno),
                arrival_time=arrival_time,
            )
            wait_cars = queue_estimate.wait_vehicles
            wait_time_minutes = queue_estimate.estimated_wait_minutes
            if queue_estimate.service_available:
                wait_score = 100.0 * math.exp(
                    -wait_time_minutes / WAIT_SCORE_DECAY_MINUTES
                )
            else:
                wait_score = 0.0

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

            final_score *= queue_estimate.availability_multiplier

            # Reduce score significantly if unreachable
            if not is_reachable:
                # Apply heavy penalty but keep in the list for visualization
                final_score *= 0.1

            rounded_scores = SubScores(
                price=round(price_score, 1),
                waiting_time=round(wait_score, 1),
                distance=round(dist_score, 1),
                facilities=round(fac_score, 1),
            )
            rounded_final_score = round(final_score, 1)
            rounded_distance_to_station = round(dist_to_st, 2)
            rounded_distance_to_destination = round(cand["dist_to_dest"], 2)
            rounded_detour = round(detour, 2)
            station_address = st.road_nm_addr or st.lotno_addr

            # Collect the facts needed to build the recommendation reason message later.
            reason_facts = StationReasonFacts(
                chrstn_nm=st.chrstn_nm,
                price_val=price_val,
                min_price=min_price,
                detour_distance=detour,
                distance_to_station=rounded_distance_to_station,
                service_available=queue_estimate.service_available,
                wait_time_minutes=wait_time_minutes,
                queue_reasons=list(queue_estimate.reasons),
                facility_count=fac_count,
                active_facilities=active_facilities,
                is_reachable=is_reachable,
            )

            scored_candidates.append(
                {
                    "model": st,
                    "lat": cand["lat"],
                    "lon": cand["lon"],
                    "station_address": station_address,
                    "distance_to_station": rounded_distance_to_station,
                    "distance_to_destination": rounded_distance_to_destination,
                    "detour_distance": rounded_detour,
                    "wait_vehicles": wait_cars,
                    "wait_time_minutes": wait_time_minutes,
                    "facilities": active_facilities,
                    "is_reachable": is_reachable,
                    "sub_scores": rounded_scores,
                    "final_score": rounded_final_score,
                    "reason_facts": reason_facts,
                }
            )

        # 7. Sort by final score descending and keep the top recommendations
        scored_candidates.sort(key=lambda x: x["final_score"], reverse=True)
        top_candidates = scored_candidates[:RECOMMENDATION_RESPONSE_LIMIT]

        # 8. Generate the per-station recommendation reason message. Only this step
        #    uses the Gemini API (batched once); it falls back to deterministic
        #    rule-based phrasing if the API is unavailable or fails.
        reasons = await self.reason_service.generate_reasons(
            [item["reason_facts"] for item in top_candidates],
            weights,
        )

        limited_recommendations = []
        for item, reason in zip(top_candidates, reasons):
            st = item["model"]
            delivery_payload = self.delivery_payload_service.build(
                chrstn_mno=st.chrstn_mno,
                chrstn_nm=st.chrstn_nm,
                station_latitude=item["lat"],
                station_longitude=item["lon"],
                station_address=item["station_address"],
                ntsl_pc=st.ntsl_pc,
                distance_to_station=item["distance_to_station"],
                detour_distance=item["detour_distance"],
                wait_vehicles=item["wait_vehicles"],
                wait_time_minutes=item["wait_time_minutes"],
                facilities=item["facilities"],
                is_reachable=item["is_reachable"],
                final_score=item["final_score"],
                recommendation_reason=reason,
            )
            limited_recommendations.append(
                RecommendedStationResponse(
                    chrstn_mno=st.chrstn_mno,
                    chrstn_nm=st.chrstn_nm,
                    road_nm_addr=item["station_address"],
                    ntsl_pc=st.ntsl_pc,
                    distance_to_station=item["distance_to_station"],
                    distance_to_destination=item["distance_to_destination"],
                    detour_distance=item["detour_distance"],
                    wait_vehicles=item["wait_vehicles"],
                    wait_time_minutes=item["wait_time_minutes"],
                    facilities=item["facilities"],
                    is_reachable=item["is_reachable"],
                    sub_scores=item["sub_scores"],
                    final_score=item["final_score"],
                    recommendation_reason=reason,
                    delivery_payload=delivery_payload,
                )
            )

        # 9. Record the top recommendations in history for analytics (up to top 5)
        top_recs = limited_recommendations
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
                        price_score=Decimal(str(r.sub_scores.price)),
                        waiting_time_score=Decimal(str(r.sub_scores.waiting_time)),
                        distance_score=Decimal(str(r.sub_scores.distance)),
                        facilities_score=Decimal(str(r.sub_scores.facilities)),
                        estimated_arrival_time=int(
                            r.distance_to_station * ROUTE_MINUTES_PER_KM
                        ),
                        selected=False,
                        selected_at=None,
                        recommendation_type="PERSONALIZED" if not request.nl_query else "RULE_BASED_FILTER",
                    )
                    for r in top_recs
                ]
            )
            # Commit background recommendation logs asynchronously
            await recommendation_history_repo.create_recommendation_histories(self.db, history_payload)

        return limited_recommendations
