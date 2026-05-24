import logging
import os
import sys

import httpx

from app.core.config import load_env
from app.core.database import async_session
from app.services.hydrogen_station_facilities_service import (
    HydrogenStationFacilitiesService,
)
from app.services.hydrogen_station_service import HydrogenStationService
from app.services.hydrogen_station_status_service import HydrogenStationStatusService


load_env()

logger = logging.getLogger(__name__)


def _env_enabled(name: str, default: bool = True) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _hying_configured(endpoint_name: str) -> bool:
    return bool(os.getenv("HYING_API_BASE_URL") and os.getenv(endpoint_name))


def _page_params(prefix: str) -> dict | None:
    params = {}
    page_no = os.getenv(f"{prefix}_PAGE_NO")
    num_of_rows = os.getenv(f"{prefix}_NUM_OF_ROWS")

    if page_no:
        params["pageNo"] = int(page_no)
    if num_of_rows:
        params["numOfRows"] = int(num_of_rows)

    return params or None


async def sync_hying_hydrogen_data_on_startup() -> None:
    if not _env_enabled("HYING_STARTUP_SYNC_ENABLED", default=True):
        logger.info("HYING_STARTUP_SYNC_ENABLED is disabled. Skipping Hying startup sync.")
        return

    async with async_session() as db:
        if _hying_configured("HYING_STATIONS_ENDPOINT"):
            try:
                result = await HydrogenStationService(db).sync_from_hying(
                    _page_params("HYING_STATIONS_SYNC")
                )
                logger.info("Hying stations startup sync completed: %s", result)
            except Exception:
                await db.rollback()
                _log_hying_sync_exception(
                    "Hying stations startup sync failed",
                    "HYING_STATIONS_ENDPOINT",
                )

        if _hying_configured("HYING_STATION_FACILITIES_ENDPOINT"):
            try:
                result = await HydrogenStationFacilitiesService(db).sync_from_hying()
                logger.info("Hying facilities startup sync completed: %s", result)
            except Exception:
                await db.rollback()
                _log_hying_sync_exception(
                    "Hying facilities startup sync failed",
                    "HYING_STATION_FACILITIES_ENDPOINT",
                )

        if _hying_configured("HYING_STATION_STATUS_ENDPOINT"):
            try:
                result = await HydrogenStationStatusService(db).sync_from_hying(
                    _page_params("HYING_STATUS_SYNC")
                )
                logger.info("Hying status startup sync completed: %s", result)
            except Exception:
                await db.rollback()
                _log_hying_sync_exception(
                    "Hying status startup sync failed",
                    "HYING_STATION_STATUS_ENDPOINT",
                )


def _log_hying_sync_exception(message: str, endpoint_env_name: str) -> None:
    exc = sys.exc_info()[1]
    if isinstance(exc, httpx.HTTPStatusError):
        response = exc.response
        if 300 <= response.status_code < 400:
            logger.error(
                "%s: Hying endpoint redirected with %s to %s. Check %s.",
                message,
                response.status_code,
                response.headers.get("location"),
                endpoint_env_name,
            )
            return

    logger.exception(message)
