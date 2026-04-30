from sqlalchemy import Column, Integer, ForeignKey, DATE, DATETIME, Numeric, func
from sqlalchemy.dialects.mssql import TIMESTAMP

from app.core.database import Base


class charging_log(Base):
    __tablename__ = 'charging_log'

    charging_log_id = Column(Integer, autoincrement=True, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    hydrogen_station_id = Column(Integer, ForeignKey('hydrogen_stations.hydrogen_station_id'), nullable=False)
    vehicle_id = Column(Integer, ForeignKey('vehicles.vehicle_id'), nullable=False)
    start_time = Column(DATETIME, nullable=False)
    end_time = Column(DATETIME, nullable=False)
    charged_amount = Column(Numeric(6, 2))
    charging_cost = Column(Numeric(10, 2))
    waiting_time = Column(Integer)
    created_at = Column(TIMESTAMP, server_default=func.now())