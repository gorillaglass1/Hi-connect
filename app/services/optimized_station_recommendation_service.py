import asyncio
import json
import math
import time
from dataclasses import dataclass
from typing import Any
from urllib import request as urllib_request
from urllib.error import URLError

from app.core.gemini_config import get_gemini_api_key, get_gemini_model
from app.schemas.optimized_station_recommendation_schema import (
    CandidateStation,
    DecisionFactors,
    GeminiRecommendationText,
    OptimizedStationRecommendationRequest,
    OptimizedStationRecommendationResponse,
    RecommendedStation,
    AlternativeStation,
)


@dataclass
class ScoredStation:
    station: CandidateStation
    score: float
    reachable: bool
    estimated_arrival_range_km: int
    supports_700bar: bool
    selected_charger_id: int | None
    reason: str


class OptimizedStationRecommendationService:
    async def recommend(
        self,
        payload: OptimizedStationRecommendationRequest,
    ) -> OptimizedStationRecommendationResponse:
        scored = self._score_candidates(payload)
        if not scored:
            raise ValueError("추천 가능한 충전소 후보가 없습니다.")

        top_candidates = scored[:5]
        best = top_candidates[0]
        gemini_text = await self._generate_gemini_text(payload, top_candidates)

        reason = gemini_text.reason or best.reason
        message = gemini_text.message_for_driver or self._default_driver_message(best)

        return OptimizedStationRecommendationResponse(
            recommendation_id=int(time.time() * 1000),
            recommended_station=RecommendedStation(
                hydrogen_station_id=best.station.hydrogen_station_id,
                name=best.station.name,
                address=best.station.address,
                latitude=best.station.latitude,
                longitude=best.station.longitude,
                selected_charger_id=best.selected_charger_id,
            ),
            score=best.score,
            reason=reason,
            decision_factors=self._decision_factors(best),
            alternatives=[
                AlternativeStation(
                    hydrogen_station_id=item.station.hydrogen_station_id,
                    name=item.station.name,
                    score=item.score,
                    reason=item.reason,
                )
                for item in scored[1:4]
            ],
            message_for_driver=message,
        )

    def _score_candidates(
        self,
        payload: OptimizedStationRecommendationRequest,
    ) -> list[ScoredStation]:
        scored: list[ScoredStation] = []
        for station in payload.candidate_stations:
            status = (station.realtime.station_status if station.realtime else None) or "UNKNOWN"
            if status.upper() not in {"OPEN", "UNKNOWN"}:
                continue

            distance = station.distance_from_current_km
            if distance is None:
                distance = self._haversine_km(
                    payload.location.latitude,
                    payload.location.longitude,
                    station.latitude,
                    station.longitude,
                )

            estimated_arrival_range = int(round(payload.vehicle.remaining_range_km - distance))
            reachable = estimated_arrival_range >= 0
            if not reachable:
                continue

            detour = station.detour_distance_km
            if detour is not None and detour > payload.preferences.max_detour_km:
                continue

            supports_700bar = self._supports_700bar(station)
            selected_charger_id = self._select_charger_id(station, payload.preferences.prefer_700bar)
            wait_time = self._wait_time(station)
            price = station.price_per_kg

            score = 100.0
            score -= max(0.0, distance - 5.0) * 0.35
            if detour is not None:
                score -= detour * 1.8
            if wait_time is not None:
                score -= wait_time * 0.7
            if price is not None:
                score -= max(0, price - 9000) / 300
            if not station.is_on_route:
                score -= 5
            if payload.preferences.prefer_700bar and supports_700bar:
                score += 8
            if payload.preferences.prefer_700bar and not supports_700bar:
                score -= 12
            if status.upper() == "UNKNOWN":
                score -= 8
            if station.realtime:
                if station.realtime.available_chargers <= 0:
                    score -= 18
                if station.realtime.hydrogen_stock_kg is not None and station.realtime.hydrogen_stock_kg < 10:
                    score -= 15
                score -= station.realtime.queue_count * 2.5

            score = round(max(0.0, min(100.0, score)), 1)
            scored.append(
                ScoredStation(
                    station=station,
                    score=score,
                    reachable=reachable,
                    estimated_arrival_range_km=estimated_arrival_range,
                    supports_700bar=supports_700bar,
                    selected_charger_id=selected_charger_id,
                    reason=self._build_reason(
                        station,
                        reachable,
                        estimated_arrival_range,
                        supports_700bar,
                        wait_time,
                    ),
                )
            )

        return sorted(scored, key=lambda item: item.score, reverse=True)

    async def _generate_gemini_text(
        self,
        payload: OptimizedStationRecommendationRequest,
        candidates: list[ScoredStation],
    ) -> GeminiRecommendationText:
        api_key = get_gemini_api_key()
        if api_key is None:
            return GeminiRecommendationText()

        gemini_payload = {
            "task": "Recommend the best hydrogen charging station for the driver.",
            "driver_context": {
                "remaining_range_km": payload.vehicle.remaining_range_km,
                "remaining_hydrogen_percent": payload.vehicle.remaining_hydrogen_percent,
                "destination": (
                    payload.navigation.destination.name
                    if payload.navigation and payload.navigation.destination
                    else None
                ),
                "estimated_remaining_range_at_arrival_km": (
                    payload.navigation.estimated_remaining_range_at_arrival_km
                    if payload.navigation
                    else None
                ),
            },
            "candidates": [self._gemini_candidate(item) for item in candidates],
            "output_format": {
                "recommended_station_id": "number",
                "reason": "short Korean explanation",
                "message_for_driver": "driver-facing Korean sentence",
            },
        }

        try:
            return await asyncio.to_thread(self._call_gemini, api_key, gemini_payload)
        except (OSError, URLError, TimeoutError, json.JSONDecodeError, KeyError, ValueError):
            return GeminiRecommendationText()

    def _call_gemini(self, api_key: str, payload: dict[str, Any]) -> GeminiRecommendationText:
        model = get_gemini_model()
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent?key={api_key}"
        )
        body = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": (
                                "Return only compact JSON matching output_format. "
                                f"Input: {json.dumps(payload, ensure_ascii=False)}"
                            )
                        }
                    ]
                }
            ],
            "generationConfig": {"responseMimeType": "application/json"},
        }
        encoded = json.dumps(body, ensure_ascii=False).encode("utf-8")
        req = urllib_request.Request(
            url,
            data=encoded,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib_request.urlopen(req, timeout=3) as response:
            response_body = json.loads(response.read().decode("utf-8"))

        text = response_body["candidates"][0]["content"]["parts"][0]["text"]
        parsed = json.loads(text)
        return GeminiRecommendationText(
            recommended_station_id=parsed.get("recommended_station_id"),
            reason=parsed.get("reason"),
            message_for_driver=parsed.get("message_for_driver"),
            raw=parsed,
        )

    def _gemini_candidate(self, item: ScoredStation) -> dict[str, Any]:
        station = item.station
        return {
            "station_id": station.hydrogen_station_id,
            "name": station.name,
            "reachable": item.reachable,
            "detour_distance_km": station.detour_distance_km,
            "wait_time_min": self._wait_time(station),
            "price_per_kg": station.price_per_kg,
            "supports_700bar": item.supports_700bar,
            "status": station.realtime.station_status if station.realtime else "UNKNOWN",
            "score": item.score,
        }

    def _decision_factors(self, item: ScoredStation) -> DecisionFactors:
        station = item.station
        return DecisionFactors(
            reachable=item.reachable,
            estimated_arrival_range_km=item.estimated_arrival_range_km,
            detour_distance_km=station.detour_distance_km,
            estimated_wait_time_min=self._wait_time(station),
            price_per_kg=station.price_per_kg,
            supports_700bar=item.supports_700bar,
            station_status=station.realtime.station_status if station.realtime else None,
        )

    def _build_reason(
        self,
        station: CandidateStation,
        reachable: bool,
        estimated_arrival_range_km: int,
        supports_700bar: bool,
        wait_time: int | None,
    ) -> str:
        parts = []
        if reachable:
            parts.append(f"현재 주행가능거리로 도달 가능하며 도착 예상 잔여거리는 {estimated_arrival_range_km}km입니다")
        if station.detour_distance_km is not None:
            parts.append(f"경로 이탈 거리는 {station.detour_distance_km:g}km입니다")
        if supports_700bar:
            parts.append("700bar 충전을 지원합니다")
        if wait_time is not None:
            parts.append(f"예상 대기 시간은 {wait_time}분입니다")
        return ", ".join(parts) + "."

    def _default_driver_message(self, item: ScoredStation) -> str:
        distance = item.station.distance_from_current_km
        wait_time = self._wait_time(item.station)
        distance_text = f"약 {distance:g}km 전방 " if distance is not None else ""
        wait_text = f" 예상 대기 시간은 {wait_time}분입니다." if wait_time is not None else ""
        return f"{distance_text}{item.station.name}을 추천합니다.{wait_text}"

    def _wait_time(self, station: CandidateStation) -> int | None:
        if station.realtime is None:
            return None
        if station.realtime.avg_wait_time is not None:
            return station.realtime.avg_wait_time
        return station.realtime.queue_count * 5

    def _supports_700bar(self, station: CandidateStation) -> bool:
        return any(
            charger.hydrogen_pressure_bar == 700 or charger.pressure_type == "700bar"
            for charger in station.chargers
        )

    def _select_charger_id(self, station: CandidateStation, prefer_700bar: bool) -> int | None:
        available = [
            charger
            for charger in station.chargers
            if charger.charger_status.upper() == "AVAILABLE"
        ]
        if not available:
            return station.chargers[0].hydrogen_charger_id if station.chargers else None
        if prefer_700bar:
            for charger in available:
                if charger.hydrogen_pressure_bar == 700 or charger.pressure_type == "700bar":
                    return charger.hydrogen_charger_id
        return available[0].hydrogen_charger_id

    def _haversine_km(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        earth_radius_km = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlon / 2) ** 2
        )
        return earth_radius_km * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
