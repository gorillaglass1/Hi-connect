from contextlib import nullcontext
from decimal import Decimal


from sqlalchemy import Column, Integer, String, TIMESTAMP, func, TIME

from app.core.database import Base

class hydrogen_station(Base):
    __tablename__ = 'hydrogen_station'
    hydrogen_station_id = Column(Integer,primary_key = True, autoincrement=True)


    name = Column(String(100), nullable=  False)
    address = Column(String(255), nullable = False)
    latitude = Column(Decimal(10, 7), nullable = False)
    longitude = Column(Decimal(10, 7), nullable = False)
    contact_number = Column(String(30))
    start_time = Column(TIME)
    end_time = Column(TIME)
    total_chargers = Column(Integer, defalt = 0)
    payment_supported = Column(String(50))
