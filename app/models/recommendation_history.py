from sqlalchemy import Column,Integer,ForeignKey,Numeric,String,Boolean,DateTime,func
from sqlalchemy.dialects.mssql import TIMESTAMP
from sqlalchemy.sql.functions import current_timestamp

from app.core.database import Base


class recommendation_history(Base):
    __tablename__ = "recommendation_history"

    recommendation_id = Column(Integer,primary_key=True,autoincrement=True)
    user_id = Column(Integer,ForeignKey('users.user_id'),nullable=False)
    vehicle_id = Column(Integer,ForeignKey('vehicles.vehicle_id'),nullable = False)
    hydrogen_station_id = Column(Integer,ForeignKey('stations.station_id'),nullable = False)
    recommendation_score = Column(Numeric(5, 2))
    recommendation_reason = Column(String(255))
    user_latitude = Column(Numeric(10, 7))
    user_longitude = Column(Numeric(10, 7))
    vehicle_remaining_hydrogen = Column(Numeric(6, 2))
    estimated_arrival_time = Column(Integer)
    selected = Column(Boolean,default=False)
    selected_at = Column(DateTime)
    recommendation_type = Column(String(50))
    created_at = Column(TIMESTAMP,server_default=func.now())
