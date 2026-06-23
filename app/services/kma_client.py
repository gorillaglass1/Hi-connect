import math
import os
from datetime import datetime, timedelta
from typing import Any

import httpx
from fastapi import HTTPException

from app.core.config import load_env


load_env()

# 기상청 공식 LCC DFS 격자 변환 상수
RE = 6371.00877  # 지구 반경(km)
GRID = 5.0       # 격자 간격(km)
SLAT1 = 30.0     # 표준위도 1
SLAT2 = 60.0     # 표준위도 2
OLON = 126.0     # 기준점 경도
OLAT = 38.0      # 기준점 위도
XO = 43          # 기준점 X좌표
YO = 136         # 기준점 Y좌표

# getVilageFcst 발표 시각
BASE_TIMES = ["0200", "0500", "0800", "1100", "1400", "1700", "2000", "2300"]
# 발표 후 API 반영 지연(분)
API_DELAY_MINUTES = 10


def convert_lat_lon_to_grid(lat: float, lon: float) -> tuple[int, int]:
    """위경도 → 기상청 격자좌표(nx, ny). LCC DFS 알고리즘."""
    degrad = math.pi / 180.0

    re = RE / GRID
    slat1 = SLAT1 * degrad
    slat2 = SLAT2 * degrad
    olon = OLON * degrad
    olat = OLAT * degrad

    sn = math.tan(math.pi * 0.25 + slat2 * 0.5) / math.tan(math.pi * 0.25 + slat1 * 0.5)
    sn = math.log(math.cos(slat1) / math.cos(slat2)) / math.log(sn)
    sf = math.tan(math.pi * 0.25 + slat1 * 0.5)
    sf = math.pow(sf, sn) * math.cos(slat1) / sn
    ro = math.tan(math.pi * 0.25 + olat * 0.5)
    ro = re * sf / math.pow(ro, sn)

    ra = math.tan(math.pi * 0.25 + lat * degrad * 0.5)
    ra = re * sf / math.pow(ra, sn)
    theta = lon * degrad - olon
    if theta > math.pi:
        theta -= 2.0 * math.pi
    if theta < -math.pi:
        theta += 2.0 * math.pi
    theta *= sn

    nx = int(ra * math.sin(theta) + XO + 0.5)
    ny = int(ro - ra * math.cos(theta) + YO + 0.5)
    return nx, ny


class KmaClient:
    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: float = 15.0,
    ):
        self.base_url = (base_url or os.getenv("KMA_API_BASE_URL") or "").rstrip("/")
        self.api_key = api_key if api_key is not None else os.getenv("KMA_API_KEY")
        self.timeout = timeout

    def compute_base_datetime(self, now: datetime | None = None) -> tuple[str, str]:
        """현재 시각 기준 가장 최근 발표분의 base_date/base_time 계산."""
        now = now or datetime.now()
        # 발표 후 API 반영 지연을 고려해 기준 시각을 지연분만큼 앞당김
        ref = now - timedelta(minutes=API_DELAY_MINUTES)
        hhmm = ref.strftime("%H%M")

        available = [bt for bt in BASE_TIMES if bt <= hhmm]
        if available:
            base_time = available[-1]
            base_date = ref.strftime("%Y%m%d")
        else:
            # 자정 직후 등 당일 발표분이 없으면 전날 마지막 발표(2300)
            base_time = BASE_TIMES[-1]
            base_date = (ref - timedelta(days=1)).strftime("%Y%m%d")
        return base_date, base_time

    async def get_vilage_fcst(self, lat: float, lon: float) -> dict[str, Any]:
        """getVilageFcst 호출. (items, base_date, base_time, nx, ny) 정보 반환."""
        if not self.base_url or not self.api_key:
            raise HTTPException(
                status_code=503,
                detail="KMA API base URL or API key is not configured",
            )

        nx, ny = convert_lat_lon_to_grid(lat, lon)
        base_date, base_time = self.compute_base_datetime()

        params = {
            "serviceKey": self.api_key,
            "pageNo": 1,
            "numOfRows": 1000,
            "dataType": "JSON",
            "base_date": base_date,
            "base_time": base_time,
            "nx": nx,
            "ny": ny,
        }

        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
                response = await client.get("/getVilageFcst", params=params)
                response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise HTTPException(
                status_code=504,
                detail="KMA API request timed out",
            ) from exc
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=502,
                detail=f"KMA API request failed: {exc}",
            ) from exc

        payload = response.json()
        header = (
            payload.get("response", {}).get("header", {})
            if isinstance(payload, dict)
            else {}
        )
        result_code = header.get("resultCode")
        if result_code != "00":
            result_msg = header.get("resultMsg", "unknown error")
            raise HTTPException(
                status_code=502,
                detail=f"KMA API error: resultCode={result_code}, resultMsg={result_msg}",
            )

        items = (
            payload.get("response", {})
            .get("body", {})
            .get("items", {})
            .get("item", [])
        )

        return {
            "items": items,
            "base_date": base_date,
            "base_time": base_time,
            "nx": nx,
            "ny": ny,
        }
