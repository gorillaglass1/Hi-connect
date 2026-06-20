from app.schemas.recommendation_schema import (
    RecommendationDeliveryPayload,
)


class RecommendationDeliveryPayloadService:
    """Creates the JSON contract that can be sent to external route/navigation systems."""

    @staticmethod
    def build(
        *,
        chrstn_mno: str,
        chrstn_nm: str,
        oper_sttus_nm: str,
        pressure_info: str,
        station_latitude: float,
        station_longitude: float,
        station_address: str | None,
        vhcle_knd_cd: str | None,
        vhcle_knd_nm: str | None,
        ntsl_pc: int | None,
        distance_to_station: float,
        detour_distance: float,
        wait_vehicles: int,
        wait_time_minutes: int,
        facilities: list[str],
        is_reachable: bool,
        final_score: float,
        recommendation_reason: str,
    ) -> RecommendationDeliveryPayload:
        return RecommendationDeliveryPayload(
            chrstn_mno=chrstn_mno,
            chrstn_nm=chrstn_nm,
            road_nm_addr=station_address,
            oper_sttus_nm=oper_sttus_nm,
            pressure_info=pressure_info,
            latitude=station_latitude,
            longitude=station_longitude,
            vhcle_knd_cd=vhcle_knd_cd,
            vhcle_knd_nm=vhcle_knd_nm,
            ntsl_pc=ntsl_pc,
            distance_to_station=distance_to_station,
            detour_distance=detour_distance,
            wait_vehicles=wait_vehicles,
            wait_time_minutes=wait_time_minutes,
            facilities=facilities,
            is_reachable=is_reachable,
            final_score=final_score,
            recommendation_reason=recommendation_reason,
        )
