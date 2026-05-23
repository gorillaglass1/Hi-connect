from sqlalchemy import Column, DateTime, Integer, String, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, autoincrement=True, comment="사용자 고유 ID")
    name = Column(String(50), nullable=False, comment="사용자 이름")
    phone = Column(String(20), comment="사용자 전화번호")
    email = Column(String(255), unique=True, comment="사용자 이메일")
    created_at = Column(DateTime, server_default=func.now(), comment="가입 일시")

    # 관계 설정
    preferences = relationship(
        "UserPreference",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
