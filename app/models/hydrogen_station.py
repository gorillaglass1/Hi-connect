from sqlalchemy import Column, Integer, Numeric, String, TIME

from app.core.database import Base


class hydrogen_station(Base):
    __tablename__ = "hydrogen_station"

    hydrogen_station_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    address = Column(String(255), nullable=False)
    latitude = Column(Numeric(10, 7), nullable=False)
    longitude = Column(Numeric(10, 7), nullable=False)
    contact_number = Column(String(30))
    start_time = Column(TIME)
    end_time = Column(TIME)
    total_chargers = Column(Integer, default=0)
    payment_supported = Column(String(50))
