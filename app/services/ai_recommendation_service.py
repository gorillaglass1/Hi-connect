import json
import ssl
from math import asin, cos, radians, sin, sqrt
from typing import TYPE_CHECKING
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from pydantic import ValidationError

from app.core.gemini_config import get_gemini_api_key, get_gemini_model
from app.schemas.ai_recommendation_schema import (
    AIRecommendationResponse,
    AiRecommendationGeminiRequest,
    AiRecommendationRequest,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class AiRecommendationService:
    def __init__(
        self,
        db: "AsyncSession | None" = None,
        client=None,
        model: str | None = None,
    ):
        self.db = db
        self.client = client
        self.model = model or get_gemini_model()

    async def create_ai_response(
        self,
        request: AiRecommendationRequest,
    ) -> AIRecommendationResponse:
        ai_request = self.build_ai_request(request)
        candidate_stations = await self.get_candidate_stations_near_destination(
            destination_latitude=request.navigation.destination.latitude,
            destination_longitude=request.navigation.destination.longitude,
        )
        if not candidate_stations:
            raise ValueError("No hydrogen station candidates found near destination.")

        prompt = self.build_prompt(ai_request, candidate_stations)
        response_text = self.generate_content(prompt)
        return self.parse_response(response_text)

    def build_ai_request(
        self,
        request: AiRecommendationRequest,
    ) -> AiRecommendationGeminiRequest:
        return AiRecommendationGeminiRequest.from_ai_recommendation_request(request)

    async def get_candidate_stations_near_destination(
        self,
        destination_latitude: float,
        destination_longitude: float,
        radius_km: float = 20,
        limit: int = 10,
    ) -> list[dict]:
        if self.db is None:
            raise RuntimeError("Database session is required.")

        from sqlalchemy import select

        from app.models.hydrogen_charger import hydrogen_charger
        from app.models.hydrogen_station import hydrogen_station
        from app.models.hydrogen_station_realtime import HydrogenStationRealtime

        lat_delta = radius_km / 111
        lon_delta = radius_km / (111 * cos(radians(destination_latitude)))

        station_result = await self.db.execute(
            select(hydrogen_station).where(
                hydrogen_station.latitude.between(
                    destination_latitude - lat_delta,
                    destination_latitude + lat_delta,
                ),
                hydrogen_station.longitude.between(
                    destination_longitude - lon_delta,
                    destination_longitude + lon_delta,
                ),
            )
        )
        stations = station_result.scalars().all()
        station_ids = [station.hydrogen_station_id for station in stations]

        realtime_by_station_id = {}
        chargers_by_station_id = {}

        if station_ids:
            realtime_result = await self.db.execute(
                select(HydrogenStationRealtime).where(
                    HydrogenStationRealtime.hydrogen_station_id.in_(station_ids)
                )
            )
            realtime_by_station_id = {
                realtime.hydrogen_station_id: realtime
                for realtime in realtime_result.scalars().all()
            }

            charger_result = await self.db.execute(
                select(hydrogen_charger).where(
                    hydrogen_charger.hydrogen_station_id.in_(station_ids)
                )
            )
            for charger in charger_result.scalars().all():
                chargers_by_station_id.setdefault(
                    charger.hydrogen_station_id,
                    [],
                ).append(charger)

        candidates = []
        for station in stations:
            distance_km = self._haversine_km(
                destination_latitude,
                destination_longitude,
                float(station.latitude),
                float(station.longitude),
            )
            if distance_km > radius_km:
                continue

            realtime = realtime_by_station_id.get(station.hydrogen_station_id)
            chargers = chargers_by_station_id.get(station.hydrogen_station_id, [])
            candidates.append(
                {
                    "station_id": station.hydrogen_station_id,
                    "name": station.name,
                    "address": station.address,
                    "latitude": float(station.latitude),
                    "longitude": float(station.longitude),
                    "distance_from_destination_km": round(distance_km, 2),
                    "payment_supported": station.payment_supported,
                    "realtime": {
                        "available_chargers": (
                            realtime.available_chargers if realtime else 0
                        ),
                        "in_use_chargers": realtime.in_use_chargers if realtime else 0,
                        "queue_count": realtime.queue_count if realtime else 0,
                        "avg_wait_time": realtime.avg_wait_time if realtime else None,
                        "hydrogen_stock_kg": (
                            float(realtime.hydrogen_stock_kg)
                            if realtime and realtime.hydrogen_stock_kg is not None
                            else None
                        ),
                        "station_status": realtime.station_status if realtime else "UNKNOWN",
                    },
                    "chargers": [
                        {
                            "charger_id": charger.hydrogen_charger_id,
                            "charger_status": charger.charger_status,
                            "hydrogen_pressure_bar": charger.hydrogen_pressure_bar,
                            "pressure_type": charger.pressure_type,
                        }
                        for charger in chargers
                    ],
                }
            )

        return sorted(
            candidates,
            key=lambda item: item["distance_from_destination_km"],
        )[:limit]

    def build_prompt(
        self,
        request: AiRecommendationGeminiRequest,
        candidate_stations: list[dict],
    ) -> str:
        payload = {
            "driving_context": request.model_dump(mode="json"),
            "candidate_stations": candidate_stations,
        }
        response_schema = AIRecommendationResponse.model_json_schema()
        return (
            "You are a hydrogen station recommendation engine. "
            "Use only the anonymized driving context and candidate stations below. "
            "Do not return personal identifiers. "
            "Recommend only stations from candidate_stations. "
            "If price is unknown, use 0. "
            "Return JSON only, matching the response schema exactly.\n\n"
            f"Input JSON:\n{json.dumps(payload, ensure_ascii=False)}\n\n"
            f"Response JSON schema:\n{json.dumps(response_schema, ensure_ascii=False)}"
        )

    def generate_content(self, prompt: str) -> str:
        if self.client is not None:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
            )
            text = getattr(response, "text", None)
            if not text:
                raise RuntimeError("Gemini returned an empty response.")
            return text

        api_key = get_gemini_api_key()
        if api_key is None:
            raise RuntimeError("Gemini API key is not configured.")

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"response_mime_type": "application/json"},
        }
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{quote(self.model, safe='')}:generateContent?key={quote(api_key, safe='')}"
        )
        request = Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlopen(
                request,
                timeout=30,
                context=self._create_ssl_context(),
            ) as response:
                body = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Gemini HTTP error: {exc.code} {detail}") from exc
        except URLError as exc:
            raise RuntimeError(f"Gemini request failed: {exc.reason}") from exc

        try:
            return body["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as exc:
            raise RuntimeError("Gemini returned an unexpected response shape.") from exc

    def _create_ssl_context(self) -> ssl.SSLContext:
        try:
            import certifi

            return ssl.create_default_context(cafile=certifi.where())
        except ImportError:
            return ssl.create_default_context()

    def parse_response(self, response_text: str) -> AIRecommendationResponse:
        try:
            return AIRecommendationResponse.model_validate_json(
                self._extract_json(response_text)
            )
        except ValidationError as exc:
            raise ValueError("Gemini response does not match AIRecommendationResponse.") from exc

    def _extract_json(self, text: str) -> str:
        stripped = text.strip()
        if stripped.startswith("```"):
            stripped = stripped.removeprefix("```json").removeprefix("```").strip()
            stripped = stripped.removesuffix("```").strip()

        if stripped.startswith("{"):
            return stripped

        decoded = json.loads(stripped)
        return json.dumps(decoded, ensure_ascii=False)

    def _haversine_km(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
    ) -> float:
        earth_radius_km = 6371.0
        d_lat = radians(lat2 - lat1)
        d_lon = radians(lon2 - lon1)
        a = (
            sin(d_lat / 2) ** 2
            + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
        )
        return earth_radius_km * 2 * asin(sqrt(a))


AIRecommendationService = AiRecommendationService
