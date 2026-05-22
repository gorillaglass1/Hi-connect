from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import hydrogen_station_status_repo
from app.schemas.hydrogen_station_status_schemas import HydrogenStationStatusCreate
from app.services.hying_client import HyingClient


class HydrogenStationStatusService:
    def __init__(self, db: AsyncSession, hying_client: HyingClient | None = None):
        self.db = db
        self.hying_client = hying_client or HyingClient()

    async def create_hydrogen_station_status(self, payload: HydrogenStationStatusCreate):
        return await hydrogen_station_status_repo.create_hydrogen_station_status(
            self.db, payload
        )

    async def get_hydrogen_station_statuses(
        self,
        chrstn_mno: str | None = None,
        oper_sttus_cd: str | None = None,
        pos_sttus_cd: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ):
        return await hydrogen_station_status_repo.get_hydrogen_station_statuses(
            self.db,
            chrstn_mno=chrstn_mno,
            oper_sttus_cd=oper_sttus_cd,
            pos_sttus_cd=pos_sttus_cd,
            limit=limit,
            offset=offset,
        )

    async def sync_from_hying(self, params: dict | None = None):
        items = await self.hying_client.fetch_station_statuses(params)
        payloads = [HydrogenStationStatusCreate.model_validate(item) for item in items]
        rows = await hydrogen_station_status_repo.upsert_hydrogen_station_statuses(
            self.db, payloads
        )
        return {
            "fetched": len(items),
            "saved": len(rows),
            "skipped": len(items) - len(rows),
        }
