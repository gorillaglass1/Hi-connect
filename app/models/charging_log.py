from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, TIMESTAMP, func

from app.core.database import Base


class ChargingLog(Base):
    __tablename__ = "charging_log"

    charging_log_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    hydrogen_station_id = Column(
        Integer, ForeignKey("hydrogen_station.hydrogen_station_id"), nullable=False
    )
    vehicle_id = Column(Integer, ForeignKey("vehicles.vehicle_id"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    charged_amount = Column(Numeric(6, 2))
    charging_cost = Column(Numeric(10, 2))
    waiting_time = Column(Integer)
    created_at = Column(TIMESTAMP, server_default=func.now())
