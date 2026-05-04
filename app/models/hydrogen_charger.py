from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String

from app.core.database import Base


class hydrogen_charger(Base):
    __tablename__ = "hydrogen_charger"

    hydrogen_charger_id = Column(Integer, primary_key=True, autoincrement=True)
    hydrogen_station_id = Column(
        Integer,
        ForeignKey("hydrogen_station.hydrogen_station_id", ondelete="CASCADE"),
        nullable=False,
    )
    charger_status = Column(Enum("충분", "여유", "부족"), nullable=False)
    charger_type = Column(String(50))
    hydrogen_pressure_bar = Column(Integer)
    pressure_type = Column(Enum("350bar", "700bar"), nullable=False)
    restock_schedule = Column(DateTime, nullable=True)
