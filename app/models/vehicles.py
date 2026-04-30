from sqlalchemy import Column, ForeignKey, String, Numeric, TIMESTAMP, func, Integer

from app.core.database import Base


class Vehicles(Base):
    __tablename__ = "vehicles"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user.id'), nullable=False)
    vehicle_number = Column(String(20), nullable=False, unique=True)
    model = Column(String(50), nullable=False)
    vehicle_type = Column(String(50), nullable=False)
    fuel_type = Column(String(50), default='hydrogen')
    tank_capacity = Column(Numeric(6, 2), nullable=False)
    avg_efficiency = Column(Numeric(6, 2))
    registered_at = Column(TIMESTAMP, server_default=func.now())