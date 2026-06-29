from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric
from sqlalchemy.orm import relationship

from app.core.database import Base


class UserPreference(Base):
    __tablename__ = "user_preferences"

    user_id = Column(
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        primary_key=True,
        comment="사용자 고유 ID (외래키)",
    )
    weight_price = Column(Numeric(4, 2), default=1.0, comment="가격 가중치")
    weight_waiting_time = Column(Numeric(4, 2), default=1.0, comment="대기시간(차량대수) 가중치")
    weight_distance = Column(Numeric(4, 2), default=1.0, comment="우회거리 가중치")
    weight_facilities = Column(Numeric(4, 2), default=1.0, comment="편의시설 가중치")
    safety_margin = Column(Numeric(4, 2), default=1.1, comment="주행가능거리 최소 안전 계수")
    created_at = Column(DateTime, default=lambda: datetime.now().astimezone(None), comment="생성 일시")
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now().astimezone(None),
        onupdate=lambda: datetime.now().astimezone(None),
        comment="수정 일시",
    )

    user = relationship("User", back_populates="preferences")
