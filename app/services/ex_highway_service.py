import logging
from typing import Any

from app.schemas.ex_highway_schema import (
    RealtimeTrafficItem,
    RealtimeTrafficResponse,
    RestAreaWeatherItem,
    RestAreaWeatherResponse,
)
from app.services.ex_highway_client import ExHighwayClient

logger = logging.getLogger("ex_highway_service")

# data.ex.co.kr 응답에서 항목 배열이 담길 수 있는 키 후보.
_LIST_KEYS = (
    "list",
    "weatherList",
    "realWeatherList",
    "restWeatherList",
    "trafficList",
    "realtimeTrafficList",
    "trafficAmountList",
    "data",
    "items",
)


class ExHighwayService:
    """한국도로공사 OpenAPI 조회 결과를 화면 전송용 스키마로 가공하는 서비스 레이어.

    DB 저장 없이 외부 API를 그대로 조회/정규화해서 반환한다.
    """

    def __init__(self, client: ExHighwayClient | None = None):
        self.client = client or ExHighwayClient()

    async def get_rest_area_weather(
        self,
        sdate: str,
        std_hour: str,
        extra_params: dict[str, Any] | None = None,
    ) -> RestAreaWeatherResponse:
        logger.info("Fetching rest area weather: sdate=%s stdHour=%s", sdate, std_hour)
        payload = await self.client.fetch_rest_area_weather(sdate, std_hour, extra_params)
        items = [
            RestAreaWeatherItem.model_validate(row)
            for row in self._extract_items(payload)
        ]
        return RestAreaWeatherResponse(
            code=self._get_str(payload, "code"),
            message=self._get_str(payload, "message"),
            count=self._get_count(payload, len(items)),
            items=items,
        )

    async def get_realtime_traffic(
        self,
        extra_params: dict[str, Any] | None = None,
    ) -> RealtimeTrafficResponse:
        logger.info("Fetching realtime traffic amount")
        payload = await self.client.fetch_realtime_traffic(extra_params)
        items = [
            RealtimeTrafficItem.model_validate(row)
            for row in self._extract_items(payload)
        ]
        return RealtimeTrafficResponse(
            code=self._get_str(payload, "code"),
            message=self._get_str(payload, "message"),
            count=self._get_count(payload, len(items)),
            items=items,
        )

    def _extract_items(self, payload: Any) -> list[dict]:
        if isinstance(payload, list):
            return [row for row in payload if isinstance(row, dict)]
        if not isinstance(payload, dict):
            return []

        for key in _LIST_KEYS:
            value = payload.get(key)
            if isinstance(value, list):
                return [row for row in value if isinstance(row, dict)]

        # 알려진 키가 없으면 dict 리스트인 첫 번째 값을 사용한다.
        for value in payload.values():
            if isinstance(value, list) and any(isinstance(row, dict) for row in value):
                return [row for row in value if isinstance(row, dict)]
        return []

    @staticmethod
    def _get_str(payload: Any, key: str) -> str | None:
        if isinstance(payload, dict) and payload.get(key) is not None:
            return str(payload[key])
        return None

    @staticmethod
    def _get_count(payload: Any, fallback: int) -> int:
        if isinstance(payload, dict) and payload.get("count") is not None:
            try:
                return int(payload["count"])
            except (TypeError, ValueError):
                return fallback
        return fallback
