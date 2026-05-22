from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class ChargingLog(Base):
    __tablename__ = "charging_log"

    charging_log_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    vehicle_id = Column(Integer, nullable=False)
    chrstn_mno = Column(
        String(30),
        ForeignKey("hydrogen_stations.chrstn_mno", ondelete="CASCADE"),
        nullable=False,
    )
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    charged_amount = Column(Numeric(6, 2))
    charging_cost = Column(Numeric(10, 2))
    waiting_time = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())

    station = relationship("HydrogenStation")
