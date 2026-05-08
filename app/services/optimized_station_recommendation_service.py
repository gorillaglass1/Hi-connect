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
    RecommendedStationOption,
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
        payload = self._with_demo_candidates(payload)
        scored = self._score_candidates(payload)
        if not scored:
            raise ValueError("추천 가능한 충전소 후보가 없습니다.")

        top_candidates = scored[:5]
        gemini_text = await self._generate_gemini_text(payload, top_candidates)
        best = self._select_ai_recommended_candidate(top_candidates, gemini_text)
        ranked_candidates = [best] + [item for item in top_candidates if item is not best]
        ranked_candidates = ranked_candidates[:3]

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
            recommendations=[
                RecommendedStationOption(
                    rank=index + 1,
                    hydrogen_station_id=item.station.hydrogen_station_id,
                    name=item.station.name,
                    address=item.station.address,
                    latitude=item.station.latitude,
                    longitude=item.station.longitude,
                    selected_charger_id=item.selected_charger_id,
                    score=item.score,
                    reason=reason if index == 0 else item.reason,
                    highlight=self._highlight(item),
                    decision_factors=self._decision_factors(item),
                )
                for index, item in enumerate(ranked_candidates)
            ],
            alternatives=[
                AlternativeStation(
                    hydrogen_station_id=item.station.hydrogen_station_id,
                    name=item.station.name,
                    score=item.score,
                    reason=item.reason,
                )
                for item in ranked_candidates[1:]
            ],
            message_for_driver=message,
        )

    def _with_demo_candidates(
        self,
        payload: OptimizedStationRecommendationRequest,
    ) -> OptimizedStationRecommendationRequest:
        if len(payload.candidate_stations) >= 3:
            return payload

        existing_ids = {station.hydrogen_station_id for station in payload.candidate_stations}
        stations = list(payload.candidate_stations)
        for station in self._demo_candidates():
            if len(stations) >= 3:
                break
            if station.hydrogen_station_id in existing_ids:
                continue
            stations.append(station)

        return payload.model_copy(update={"candidate_stations": stations})

    def _demo_candidates(self) -> list[CandidateStation]:
        return [
            CandidateStation(
                hydrogen_station_id=901,
                name="데모 강동 수소스테이션",
                address="서울 강동구 데모로 12",
                latitude=37.5301,
                longitude=127.1238,
                distance_from_current_km=14.2,
                detour_distance_km=4.5,
                is_on_route=True,
                price_per_kg=8800,
                payment_supported="card",
                realtime={
                    "available_chargers": 1,
                    "in_use_chargers": 0,
                    "queue_count": 1,
                    "avg_wait_time": 5,
                    "hydrogen_stock_kg": 80,
                    "station_status": "OPEN",
                },
                chargers=[
                    {
                        "hydrogen_charger_id": 9001,
                        "charger_status": "AVAILABLE",
                        "hydrogen_pressure_bar": 700,
                        "pressure_type": "700bar",
                    }
                ],
            ),
            CandidateStation(
                hydrogen_station_id=902,
                name="데모 하남 수소충전소",
                address="경기 하남시 데모대로 77",
                latitude=37.545,
                longitude=127.205,
                distance_from_current_km=22.5,
                detour_distance_km=6.8,
                is_on_route=False,
                price_per_kg=9700,
                payment_supported="card",
                realtime={
                    "available_chargers": 2,
                    "in_use_chargers": 0,
                    "queue_count": 0,
                    "avg_wait_time": 0,
                    "hydrogen_stock_kg": 200,
                    "station_status": "OPEN",
                },
                chargers=[
                    {
                        "hydrogen_charger_id": 9002,
                        "charger_status": "AVAILABLE",
                        "hydrogen_pressure_bar": 350,
                        "pressure_type": "350bar",
                    }
                ],
            ),
            CandidateStation(
                hydrogen_station_id=903,
                name="데모 판교 수소충전소",
                address="경기 성남시 분당구 데모길 5",
                latitude=37.3947,
                longitude=127.1112,
                distance_from_current_km=19.1,
                detour_distance_km=2.8,
                is_on_route=True,
                price_per_kg=10100,
                payment_supported="card,app",
                realtime={
                    "available_chargers": 1,
                    "in_use_chargers": 1,
                    "queue_count": 2,
                    "avg_wait_time": 12,
                    "hydrogen_stock_kg": 140,
                    "station_status": "OPEN",
                },
                chargers=[
                    {
                        "hydrogen_charger_id": 9003,
                        "charger_status": "AVAILABLE",
                        "hydrogen_pressure_bar": 700,
                        "pressure_type": "700bar",
                    }
                ],
            ),
        ]

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

    def _select_ai_recommended_candidate(
        self,
        candidates: list[ScoredStation],
        gemini_text: GeminiRecommendationText,
    ) -> ScoredStation:
        if gemini_text.recommended_station_id is None:
            return candidates[0]
        return next(
            (
                item
                for item in candidates
                if item.station.hydrogen_station_id == gemini_text.recommended_station_id
            ),
            candidates[0],
        )

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

    def _highlight(self, item: ScoredStation) -> str:
        station = item.station
        wait_time = self._wait_time(station)
        if station.realtime and station.realtime.available_chargers > 0 and wait_time is not None and wait_time <= 10:
            return "대기 시간이 짧음"
        if station.price_per_kg is not None and station.price_per_kg <= 9900:
            return "수소 가격이 저렴함"
        if station.detour_distance_km is not None and station.detour_distance_km <= 3:
            return "경로 이탈 거리가 짧음"
        if item.supports_700bar:
            return "700bar 충전 지원"
        if station.realtime and station.realtime.hydrogen_stock_kg is not None and station.realtime.hydrogen_stock_kg >= 50:
            return "수소 재고가 충분함"
        return "종합 점수가 높음"

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
