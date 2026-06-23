import math

from app.schemas.weather_schema import WeatherResponse
from app.services.kma_client import KmaClient

SKY_MAP = {"1": "맑음", "3": "구름많음", "4": "흐림"}
PTY_MAP = {"0": "없음", "1": "비", "2": "비/눈", "3": "눈", "4": "소나기"}


def _calc_feels_like(temp: float, humidity: int, wind_speed: float) -> float:
    """기온/습도/풍속 기반 간단 체감온도.
    기온이 낮으면 풍속을 반영한 풍속냉각, 그 외엔 기온 그대로."""
    if temp <= 10.0 and wind_speed >= 1.34:
        v = wind_speed * 3.6  # m/s → km/h
        feels = (
            13.12
            + 0.6215 * temp
            - 11.37 * math.pow(v, 0.16)
            + 0.3965 * temp * math.pow(v, 0.16)
        )
        return round(feels, 1)
    return round(temp, 1)


class WeatherService:
    def __init__(self, kma_client: KmaClient | None = None):
        self.kma_client = kma_client or KmaClient()

    async def get_weather(self, lat: float, lon: float) -> WeatherResponse:
        result = await self.kma_client.get_vilage_fcst(lat, lon)
        items = result["items"]

        # 가장 가까운(가장 이른) fcstTime의 예보값만 사용
        fcst_times = sorted(
            {item["fcstTime"] for item in items if "fcstTime" in item}
        )
        target_time = fcst_times[0] if fcst_times else None

        values: dict[str, str] = {}
        for item in items:
            if target_time is not None and item.get("fcstTime") != target_time:
                continue
            values[item.get("category")] = item.get("fcstValue")

        temperature = float(values.get("TMP", 0.0))
        humidity = int(float(values.get("REH", 0)))
        wind_speed = float(values.get("WSD", 0.0))
        sky = SKY_MAP.get(str(values.get("SKY", "")), "알수없음")
        precipitation_type = PTY_MAP.get(str(values.get("PTY", "")), "없음")

        return WeatherResponse(
            temperature=temperature,
            sky=sky,
            precipitation_type=precipitation_type,
            humidity=humidity,
            wind_speed=wind_speed,
            feels_like=_calc_feels_like(temperature, humidity, wind_speed),
            base_time=result["base_time"],
            nx=result["nx"],
            ny=result["ny"],
        )
