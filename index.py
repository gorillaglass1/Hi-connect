from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from starlette.responses import FileResponse

from app.api.charging_log_api import router as charging_log_router
from app.api.hydrogen_charger_api import router as hydrogen_charger_router
from app.api.hydrogen_station_api import router as hydrogen_station_router
from app.api.hydrogen_station_realtime_api import router as hydrogen_station_realtime_router
from app.api.hydrogen_station_reservation_api import router as hydrogen_station_reservation_router
from app.api.recommendation_history_api import router as recommendation_history_router
from app.api.user_api import router as user_router
from app.api.vehicles_api import router as vehicles_router
from app.core.database import Base, engine
from app.core.dummy_data_loader import load_dummy_data_from_dml
from app.core.security import enforce_api_key_if_configured
from app.core.sql_bootstrap import run_startup_sql
from app.models.charging_log import ChargingLog  # noqa: F401
from app.models.hydrogen_charger import hydrogen_charger  # noqa: F401
from app.models.hydrogen_station import hydrogen_station  # noqa: F401
from app.models.hydrogen_station_realtime import HydrogenStationRealtime  # noqa: F401
from app.models.hydrogen_station_reservation import HydrogenStationReservation  # noqa: F401
from app.models.recommendation_history import recommendation_history  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.vehicles import Vehicles  # noqa: F401

@asynccontextmanager
async def lifespan(_: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await run_startup_sql(engine)
    await load_dummy_data_from_dml(engine)
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(user_router)
app.include_router(vehicles_router)
app.include_router(charging_log_router)
app.include_router(hydrogen_station_router)
app.include_router(hydrogen_charger_router)
app.include_router(hydrogen_station_realtime_router)
app.include_router(hydrogen_station_reservation_router)
app.include_router(recommendation_history_router)


@app.middleware("http")
async def api_key_guard(request: Request, call_next):
    await enforce_api_key_if_configured(request)
    return await call_next(request)


@app.get("/")
async def mainPage():
    return FileResponse("app/src/index.html")


