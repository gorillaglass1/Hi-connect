from sqlalchemy import Column, Integer, ForeignKey, DateTime, Numeric, func

from app.core.database import Base


class ChargingLog(Base):
    __tablename__ = "charging_log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    # 충전 로그 고유 ID

    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    # 충전 사용자 ID 외래키

    hydrogen_station_id = Column(Integer, ForeignKey("hydrogen_station.hydrogen_station_id"), nullable=False)
    # 충전소 ID 외래키

    vehicle_id = Column(Integer, ForeignKey("vehicles.vehicle_id"), nullable=False)
    # 충전 차량 ID 외래키

    start_time = Column(DateTime, nullable=False)
    # 충전 시작 시간

    end_time = Column(DateTime, nullable=False)
    # 충전 종료 시간

    charged_amount = Column(Numeric(6, 2))
    # 충전된 수소량(kg)

    charging_cost = Column(Numeric(10, 2))
    # 충전 비용 (KRW)

    waiting_time = Column(Integer)
    # 충전 대기시간 (Minute)

    created_at = Column(DateTime, server_default=func.now())
    # 로그 생성 시간