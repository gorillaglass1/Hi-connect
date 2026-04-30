from sqlalchemy import Column, Integer, String, TIMESTAMP, func

from app.core.database import Base

class hydrogen_station(Base):
    __tablename__ = 'hydrogen_station'
    hydrogen_station_id = Column(Integer,primary_key = True, autoincrement=True)
