import asyncio
import contextlib
import logging
import os

import httpx

from app.core.config import load_env
from app.core.database import async_session
from app.services.hydrogen_station_status_service import HydrogenStationStatusService


load_env()

logger = logging.getLogger(__name__)

DEFAULT_STATUS_SYNC_INTERVAL_SECONDS = 300


def _env_enabled(name: str, default: bool = True) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _env_int(name: str) -> int | None:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return None
    return int(value)


def status_sync_is_configured() -> bool:
    if not _env_enabled("HYING_STATUS_SYNC_ENABLED", default=True):
        return False
    return bool(
        os.getenv("HYING_API_BASE_URL")
        and os.getenv("HYING_STATION_STATUS_ENDPOINT")
    )


def status_sync_params() -> dict | None:
    params = {}
    page_no = _env_int("HYING_STATUS_SYNC_PAGE_NO")
    num_of_rows = _env_int("HYING_STATUS_SYNC_NUM_OF_ROWS")

    if page_no is not None:
        params["pageNo"] = page_no
    if num_of_rows is not None:
        params["numOfRows"] = num_of_rows

    return params or None


def status_sync_interval_seconds() -> int:
    return _env_int("HYING_STATUS_SYNC_INTERVAL_SECONDS") or (
        DEFAULT_STATUS_SYNC_INTERVAL_SECONDS
    )


async def sync_hydrogen_station_status_once() -> dict:
    async with async_session() as db:
        try:
            return await HydrogenStationStatusService(db).sync_from_hying(
                status_sync_params()
            )
        except Exception:
            await db.rollback()
            raise


async def run_hydrogen_station_status_sync_loop() -> None:
    interval = status_sync_interval_seconds()
    logger.info("Hydrogen station status sync loop started: interval=%s", interval)

    while True:
        try:
            result = await sync_hydrogen_station_status_once()
            logger.info("Hydrogen station status synced: %s", result)
        except asyncio.CancelledError:
            raise
        except httpx.HTTPStatusError as exc:
            response = exc.response
            if 300 <= response.status_code < 400:
                logger.error(
                    "Hydrogen station status sync failed: Hying endpoint redirected "
                    "with %s to %s. Check HYING_STATION_STATUS_ENDPOINT.",
                    response.status_code,
                    response.headers.get("location"),
                )
            else:
                logger.exception("Hydrogen station status sync failed")
        except Exception:
            logger.exception("Hydrogen station status sync failed")

        await asyncio.sleep(interval)


def start_hydrogen_station_status_sync_task() -> asyncio.Task | None:
    if not status_sync_is_configured():
        logger.info("Hydrogen station status sync skipped: Hying API is not configured")
        return None
    return asyncio.create_task(run_hydrogen_station_status_sync_loop())


async def stop_hydrogen_station_status_sync_task(
    task: asyncio.Task | None,
) -> None:
    if task is None:
        return

    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task
