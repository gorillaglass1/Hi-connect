import os
from typing import Any

import httpx
from fastapi import HTTPException

from app.core.config import load_env


load_env()


class HyingClient:
    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: float = 15.0,
    ):
        self.base_url = (base_url or os.getenv("HYING_API_BASE_URL") or "").rstrip("/")
        self.api_key = api_key if api_key is not None else os.getenv("HYING_API_KEY")
        self.timeout = timeout

    async def fetch_stations(self, params: dict[str, Any] | None = None) -> list[dict]:
        return await self._get(os.getenv("HYING_STATIONS_ENDPOINT"), params)

    async def fetch_station_statuses(
        self,
        params: dict[str, Any] | None = None,
    ) -> list[dict]:
        return await self._get(os.getenv("HYING_STATION_STATUS_ENDPOINT"), params)

    async def fetch_station_facilities(
        self,
        params: dict[str, Any] | None = None,
    ) -> list[dict]:
        # Hying facilities API returns the full station facilities list and does
        # not accept paging/filter params.
        return await self._get(os.getenv("HYING_STATION_FACILITIES_ENDPOINT"), None)

    async def _get(
        self,
        endpoint: str | None,
        params: dict[str, Any] | None = None,
    ) -> list[dict]:
        if not self.base_url or not endpoint:
            raise HTTPException(
                status_code=503,
                detail="Hying API base URL or endpoint is not configured",
            )

        request_params = dict(params or {})
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = self.api_key

        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            response = await client.get(
                endpoint,
                params=request_params,
                headers=headers,
            )
            response.raise_for_status()

        return self._extract_items(response.json())

    def _extract_items(self, payload: Any) -> list[dict]:
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]

        if not isinstance(payload, dict):
            return []

        if "chrstn_mno" in payload:
            return [payload]

        for key in ("items", "item", "list", "data", "result", "records"):
            value = payload.get(key)
            if value is not None:
                return self._extract_items(value)

        for key in ("response", "body"):
            value = payload.get(key)
            if value is not None:
                items = self._extract_items(value)
                if items:
                    return items

        return []
