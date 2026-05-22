from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class RecommendationHistory(Base):
    __tablename__ = "recommendation_history"

    recommendation_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    vehicle_id = Column(Integer, nullable=False)
    chrstn_mno = Column(
        String(30),
        ForeignKey("hydrogen_stations.chrstn_mno", ondelete="CASCADE"),
        nullable=False,
    )
    recommendation_score = Column(Numeric(5, 2))
    recommendation_reason = Column(String(255))
    user_latitude = Column(Numeric(10, 7))
    user_longitude = Column(Numeric(10, 7))
    vehicle_remaining_hydrogen = Column(Numeric(6, 2))
    estimated_arrival_time = Column(Integer)
    selected = Column(Boolean, default=False)
    selected_at = Column(DateTime)
    recommendation_type = Column(String(50))
    created_at = Column(DateTime, server_default=func.now())

    station = relationship("HydrogenStation")
