from sqlalchemy import Column, Integer, ForeignKey, Numeric, String, DATETIME, TIMESTAMP, func

from app.core.database import Base


class HydrogenStationRealtime(Base):
    __tablename__ = "hydrogen_station_realtime"

    realtime_id = Column(Integer, primary_key=True, autoincrement=True)
    hydrogen_station_id = Column(Integer, ForeignKey("hydrogen_station.hydrogen_station_id"), nullable=False)
    available_chargers = Column(Integer, default=0)
    in_use_chargers = Column(Integer, default=0)
    queue_count = Column(Integer, default=0)
    avg_wait_time = Column(Integer)
    hydrogen_stock_kg = Column(Numeric(8, 2))
    station_status = Column(String(50))
    last_restock_at = Column(DATETIME)
    next_restock_schedule = Column(DATETIME)
    utilization_rate = Column(Numeric(5, 2))
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
