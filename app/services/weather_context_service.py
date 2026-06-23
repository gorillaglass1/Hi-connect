"""날씨 / 대기질 컨텍스트 수집 (스켈레톤).

⚠️ 이 모듈은 "기본 틀"만 제공한다. KMA 단기예보 / AirKorea 실제 연동은
담당 개발자가 아래 TODO 지점을 채워 구현한다. 대시보드 서비스는 이 모듈이
반환하는 `WeatherContext` 형태(dict)에만 의존하므로, 내부 구현이 바뀌어도
대시보드 오케스트레이션은 영향을 받지 않는다.

채워야 할 부분:
1. latlon_to_grid(): 위경도 -> KMA 격자(nx, ny) 변환 (기상청 LCC DFS 공식).
2. fetch_short_term_forecast(): KMA 단기예보 API 호출 -> 기온/하늘/강수 등.
3. fetch_air_quality(): AirKorea API 호출 -> PM10/PM2.5/통합대기 등급.

현재는 모든 외부 호출을 건너뛰고 None/기본값을 반환한다(타임아웃/실패와 동일하게
대시보드가 정상 폴백하도록).
"""

import logging
from dataclasses import asdict, dataclass

logger = logging.getLogger("weather_context_service")


@dataclass
class WeatherContext:
    """LLM 프롬프트에 들어갈 원시 수치 묶음. 값이 없으면 None."""

    temperature_c: float | None = None      # 기온(°C)
    sky_state: str | None = None             # 하늘 상태 (맑음/구름많음/흐림 등)
    precipitation: str | None = None         # 강수 형태 (없음/비/눈 등)
    pm10: int | None = None                  # 미세먼지 농도(㎍/㎥)
    pm25: int | None = None                  # 초미세먼지 농도(㎍/㎥)
    air_grade: str | None = None             # 통합대기 등급 (좋음/보통/나쁨 등)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Grid:
    nx: int
    ny: int


class WeatherContextService:
    """위경도 기준 날씨/대기질 컨텍스트를 모은다. (현재 스켈레톤)"""

    async def collect(self, lat: float, lon: float) -> WeatherContext:
        """대시보드가 호출하는 단일 진입점.

        실패해도 예외를 던지지 않고 빈 컨텍스트를 반환해야 한다. (단일 LLM 호출
        파이프라인이 날씨 때문에 죽으면 안 됨)
        """
        try:
            grid = self.latlon_to_grid(lat, lon)
            forecast = await self.fetch_short_term_forecast(grid)
            air = await self.fetch_air_quality(lat, lon)
            return WeatherContext(**{**forecast, **air})
        except Exception as exc:  # pragma: no cover - 방어적
            logger.warning("날씨/대기질 수집 실패, 빈 컨텍스트로 폴백: %s", exc)
            return WeatherContext()

    def latlon_to_grid(self, lat: float, lon: float) -> Grid:
        """위경도 -> KMA 격자(nx, ny) 변환.

        TODO(weather-owner): 기상청 LCC DFS 변환 공식을 구현할 것.
        """
        # 스켈레톤: 실제 변환 전까지는 (0, 0) 자리표시자.
        return Grid(nx=0, ny=0)

    async def fetch_short_term_forecast(self, grid: Grid) -> dict:
        """KMA 단기예보 조회 결과(기온/하늘/강수) dict.

        TODO(weather-owner): KMA getVilageFcst 호출 및 파싱.
        반환 키: temperature_c, sky_state, precipitation
        """
        return {
            "temperature_c": None,
            "sky_state": None,
            "precipitation": None,
        }

    async def fetch_air_quality(self, lat: float, lon: float) -> dict:
        """AirKorea 대기질 조회 결과 dict.

        TODO(weather-owner): 측정소 매핑 + getMsrstnAcctoRltmMesureDnsty 호출.
        반환 키: pm10, pm25, air_grade
        """
        return {
            "pm10": None,
            "pm25": None,
            "air_grade": None,
        }
