from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.user_api import router as user_router
from app.core.database import Base, engine
from app.models.user import User  # noqa: F401

@asynccontextmanager
async def lifespan(_: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(user_router)


@app.get("/")
async def root():
    return {"message": "Hello World"}
