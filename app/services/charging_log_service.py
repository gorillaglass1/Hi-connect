from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import charging_log_repo
from app.schemas.charging_log_schema import ChargingLogCreate


class ChargingLogService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_charging_logs(self, payload: ChargingLogCreate):
        for log in payload.logs:
            if log.end_time <= log.start_time:
                raise HTTPException(
                    status_code=400,
                    detail="Charging log end_time must be after start_time",
                )

        try:
            return await charging_log_repo.create_charging_logs(self.db, payload)
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(
                status_code=400,
                detail="One or more hydrogen stations do not exist",
            )

    async def get_charging_logs(
        self,
        charging_log_id: int | None = None,
        user_id: int | None = None,
        chrstn_mno: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ):
        return await charging_log_repo.get_charging_logs(
            self.db,
            charging_log_id=charging_log_id,
            user_id=user_id,
            chrstn_mno=chrstn_mno,
            limit=limit,
            offset=offset,
        )
