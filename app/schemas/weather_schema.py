from pydantic import BaseModel


class WeatherResponse(BaseModel):
    temperature: float
    sky: str
    precipitation_type: str
    humidity: int
    wind_speed: float
    feels_like: float
    base_time: str
    nx: int
    ny: int
