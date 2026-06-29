from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, CHAR
from sqlalchemy.orm import relationship

from app.core.database import Base


class HydrogenStationAdditionalInfo(Base):
    __tablename__ = "hydrogen_station_additional_info"

    additional_info_id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="충전소 부가정보 ID",
    )

    chrstn_mno = Column(
        String(30),
        ForeignKey("hydrogen_stations.chrstn_mno", ondelete="CASCADE"),
        nullable=False,
        comment="수소충전소 관리번호",
    )

    adi_info_se_cd = Column(String(10), nullable=True, comment="부가정보 구분 코드")
    adi_info_se_nm = Column(String(50), nullable=True, comment="부가정보 구분명")

    del_at = Column(CHAR(1), default="0", comment="삭제 여부")

    last_mdfcn_dt = Column(DateTime(timezone=True), nullable=True, comment="최종 수정 일시")
    timestamp = Column(DateTime(timezone=True), nullable=True, comment="데이터 수집 또는 갱신 일시")

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now().astimezone(None), comment="DB 생성 일시")
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now().astimezone(None),
        onupdate=lambda: datetime.now().astimezone(None),
        comment="DB 수정 일시",
    )

    station = relationship(
        "HydrogenStation",
        back_populates="facilities_list",
    )