from sqlalchemy import Column, Integer, ForeignKey, String, DATETIME, TIMESTAMP, func

from app.core.database import Base


class HydrogenStationReservation(Base):
    __tablename__ = "hydrogen_station_reservation"

    hydrogen_station_reservation_id = Column(Integer, primary_key=True, autoincrement=True)
    hydrogen_charger_id = Column(Integer, ForeignKey("hydrogen_charger.hydrogen_charger_id"), nullable=False)
    hydrogen_station_id = Column(Integer, ForeignKey("hydrogen_station.hydrogen_station_id"), nullable=False)
    reservation_status = Column(String(20), nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    reservation_time = Column(DATETIME, nullable=False)
    expire_time = Column(DATETIME, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
