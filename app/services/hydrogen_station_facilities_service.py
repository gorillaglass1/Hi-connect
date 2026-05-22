from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import hydrogen_station_facilities_repo
from app.schemas.hydrogen_station_facilities import (
    HydrogenStationAdditionalInfoCreate,
)
from app.services.hying_client import HyingClient


class HydrogenStationFacilitiesService:
    def __init__(self, db: AsyncSession, hying_client: HyingClient | None = None):
        self.db = db
        self.hying_client = hying_client or HyingClient()

    async def create_hydrogen_station_facility(
        self,
        payload: HydrogenStationAdditionalInfoCreate,
    ):
        return await hydrogen_station_facilities_repo.create_hydrogen_station_facility(
            self.db, payload
        )

    async def get_hydrogen_station_facilities(
        self,
        chrstn_mno: str | None = None,
        adi_info_se_cd: str | None = None,
        del_at: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ):
        return await hydrogen_station_facilities_repo.get_hydrogen_station_facilities(
            self.db,
            chrstn_mno=chrstn_mno,
            adi_info_se_cd=adi_info_se_cd,
            del_at=del_at,
            limit=limit,
            offset=offset,
        )

    async def sync_from_hying(self):
        items = await self.hying_client.fetch_station_facilities()
        payloads = [
            HydrogenStationAdditionalInfoCreate.model_validate(item) for item in items
        ]
        rows = await hydrogen_station_facilities_repo.upsert_hydrogen_station_facilities(
            self.db, payloads
        )
        return {
            "fetched": len(items),
            "saved": len(rows),
            "skipped": len(items) - len(rows),
        }
