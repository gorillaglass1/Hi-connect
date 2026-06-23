from fastapi import APIRouter

from app.schemas.weather_schema import WeatherResponse
from app.services.weather_service import WeatherService

router = APIRouter(prefix="/weather", tags=["weather"])


@router.get("", response_model=WeatherResponse)
async def get_weather(lat: float, lon: float):
    return await WeatherService().get_weather(lat, lon)
