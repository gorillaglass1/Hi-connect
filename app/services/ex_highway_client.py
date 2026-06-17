import os
from typing import Any

import httpx
from fastapi import HTTPException

from app.core.config import load_env


load_env()


class ExHighwayClient:
    """한국도로공사 고속도로 공공데이터(data.ex.co.kr) OpenAPI 호출 클라이언트.

    인증키(EX_API_KEY)는 .env에 설정한다. 기본 base URL은 공식 도메인이다.
    """

    REST_WEATHER_PATH = "/openapi/restinfo/restWeatherList"
    REALTIME_TRAFFIC_PATH = "/openapi/odtraffic/trafficAmountByRealtime"

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: float = 15.0,
    ):
        self.base_url = (
            base_url or os.getenv("EX_API_BASE_URL") or "https://data.ex.co.kr"
        ).rstrip("/")
        self.api_key = api_key if api_key is not None else os.getenv("EX_API_KEY")
        self.timeout = timeout

    async def fetch_rest_area_weather(
        self,
        sdate: str,
        std_hour: str,
        extra_params: dict[str, Any] | None = None,
    ) -> dict:
        """휴게소별 날씨 정보 조회. sdate(날짜), stdHour(시간대)는 필수."""
        params: dict[str, Any] = {"sdate": sdate, "stdHour": std_hour}
        if extra_params:
            params.update(extra_params)
        return await self._get(self.REST_WEATHER_PATH, params)

    async def fetch_realtime_traffic(
        self,
        extra_params: dict[str, Any] | None = None,
    ) -> dict:
        """실시간 교통량 조회."""
        return await self._get(self.REALTIME_TRAFFIC_PATH, extra_params)

    async def _get(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> dict:
        if not self.api_key:
            raise HTTPException(
                status_code=503,
                detail="EX_API_KEY is not configured",
            )

        request_params: dict[str, Any] = {"key": self.api_key, "type": "json"}
        request_params.update(params or {})

        async with httpx.AsyncClient(
            base_url=self.base_url, timeout=self.timeout
        ) as client:
            response = await client.get(
                endpoint,
                params=request_params,
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()

        payload = response.json()
        return payload if isinstance(payload, dict) else {"list": payload}
