from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.responses import FileResponse

from app.api.charging_log_api import router as charging_log_router
from app.api.hydrogen_station_api import router as hydrogen_station_router
from app.api.hydrogen_station_facilities_api import (
    router as hydrogen_station_facilities_router,
)
from app.api.hydrogen_station_status_api import router as hydrogen_station_status_router
from app.api.recommendation_history_api import (
    router as recommendation_history_router,
)
from app.core.database import Base, engine
from app.core.hying_startup_sync import sync_hying_hydrogen_data_on_startup
from app.core.status_sync import (
    start_hydrogen_station_status_sync_task,
    stop_hydrogen_station_status_sync_task,
)
from app.models.charging_log import ChargingLog  # noqa: F401
from app.models.hydrogen_station_facilities import HydrogenStationAdditionalInfo  # noqa: F401
from app.models.hydrogen_station_status import HydrogenStationStatus  # noqa: F401
from app.models.hydrogen_stations import HydrogenStation  # noqa: F401
from app.models.recommendation_history import RecommendationHistory  # noqa: F401


@asynccontextmanager
async def lifespan(_: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await sync_hying_hydrogen_data_on_startup()
    status_sync_task = start_hydrogen_station_status_sync_task()
    try:
        yield
    finally:
        await stop_hydrogen_station_status_sync_task(status_sync_task)


app = FastAPI(lifespan=lifespan)
app.include_router(hydrogen_station_router)
app.include_router(hydrogen_station_status_router)
app.include_router(hydrogen_station_facilities_router)
app.include_router(recommendation_history_router)
app.include_router(charging_log_router)


@app.get("/")
async def mainPage():
    return FileResponse("app/src/index.html")
