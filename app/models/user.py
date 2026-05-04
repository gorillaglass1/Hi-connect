from sqlalchemy import Column, Integer, String, TIMESTAMP, func
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    phone = Column(String(20))
    email = Column(String(255), unique=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

