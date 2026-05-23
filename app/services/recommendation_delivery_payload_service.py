from app.schemas.recommendation_request_schemas import (
    DeliveryRouteContext,
    DeliveryStation,
    GeoPoint,
    RecommendationDeliveryPayload,
    RecommendationSearchRequest,
    SubScores,
)


class RecommendationDeliveryPayloadService:
    """Creates the JSON contract that can be sent to external route/navigation systems."""

    @staticmethod
    def build(
        *,
        request: RecommendationSearchRequest,
        recommendation_type: str,
        chrstn_mno: str,
        chrstn_nm: str,
        station_latitude: float,
        station_longitude: float,
        station_address: str | None,
        distance_to_station: float,
        distance_to_destination: float,
        detour_distance: float,
        is_reachable: bool,
        scores: SubScores,
        final_score: float,
        recommendation_reason: str,
    ) -> RecommendationDeliveryPayload:
        return RecommendationDeliveryPayload(
            user_id=request.user_id,
            recommendation_type=recommendation_type,
            station=DeliveryStation(
                chrstn_mno=chrstn_mno,
                name=chrstn_nm,
                address=station_address,
                location=GeoPoint(
                    latitude=station_latitude,
                    longitude=station_longitude,
                ),
            ),
            route_context=DeliveryRouteContext(
                current_location=GeoPoint(
                    latitude=float(request.current_latitude),
                    longitude=float(request.current_longitude),
                ),
                destination=GeoPoint(
                    latitude=float(request.destination_latitude),
                    longitude=float(request.destination_longitude),
                ),
                remaining_range_km=float(request.remaining_range),
                distance_to_station_km=distance_to_station,
                distance_to_destination_km=distance_to_destination,
                detour_distance_km=detour_distance,
                is_reachable=is_reachable,
            ),
            scores=scores,
            final_score=final_score,
            recommendation_reason=recommendation_reason,
        )
