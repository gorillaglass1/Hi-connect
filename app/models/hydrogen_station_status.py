from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class HydrogenStationStatus(Base):
    __tablename__ = "hydrogen_station_status"

    status_id = Column(Integer, primary_key=True, autoincrement=True, comment="충전소 상태 정보 ID")

    chrstn_mno = Column(
        String(30),
        ForeignKey("hydrogen_stations.chrstn_mno", ondelete="CASCADE"),
        nullable=False,
        comment="수소충전소 관리번호",
    )

    tt_pressr = Column(Integer, nullable=True, comment="총 압력")
    prfect_elctc_posbl_alge = Column(Integer, nullable=True, comment="완전 충전 가능 대수")
    wait_vhcle_alge = Column(Integer, nullable=True, comment="대기 차량 대수")

    cnf_sttus_cd = Column(String(10), nullable=True, comment="혼잡 상태 코드")
    cnf_sttus_nm = Column(String(50), nullable=True, comment="혼잡 상태명")

    oper_sttus_cd = Column(String(10), nullable=True, comment="운영 상태 코드")
    oper_sttus_nm = Column(String(50), nullable=True, comment="운영 상태명")

    pos_sttus_cd = Column(String(10), nullable=True, comment="영업 상태 코드")
    pos_sttus_nm = Column(String(50), nullable=True, comment="영업 상태명")

    last_mdfcn_dt = Column(DateTime(timezone=True), nullable=True, comment="최종 수정 일시")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now().astimezone(None), comment="DB 생성 일시")
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now().astimezone(None),
        onupdate=lambda: datetime.now().astimezone(None),
        comment="DB 수정 일시",
    )

    station = relationship("HydrogenStation", back_populates="status_list")
