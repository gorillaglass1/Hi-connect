from sqlalchemy import Column, String, Integer, Text, Time, DateTime, DECIMAL, CHAR
from sqlalchemy.orm import relationship

from app.core.database import Base


class HydrogenStation(Base):
    __tablename__ = "hydrogen_stations"

    chrstn_mno = Column(String(30), primary_key=True, comment="수소충전소 관리번호")

    chrstn_nm = Column(String(100), nullable=False, comment="수소충전소명")
    chrstn_cttpc = Column(String(30), comment="충전소 연락처")

    road_nm_addr = Column(String(255), comment="도로명 주소")
    lotno_addr = Column(String(255), comment="지번 주소")

    cmpt_yn = Column(CHAR(1), comment="복합 여부 Y/N")

    chrstn_ty_cd = Column(String(10), comment="충전소 유형 코드")
    chrstn_ty_nm = Column(String(50), comment="충전소 유형명")

    echrgeqp_ty_cd = Column(String(10), comment="충전 장비 유형 코드")
    echrgeqp_ty_nm = Column(String(100), comment="충전 장비 유형명")

    chrgr_ty_cd = Column(String(10), comment="충전기 유형 코드")
    chrgr_ty_nm = Column(String(50), comment="충전기 유형명")

    chrstn_ty_rm = Column(String(100), comment="충전소 유형 비고")

    spldmd_mn_mthd_cd = Column(String(10), comment="수급 방식 코드")
    spldmd_mn_mthd_nm = Column(String(100), comment="수급 방식명")

    event_cn = Column(Text, comment="공지사항 또는 이벤트 내용")

    vhcle_knd_cd = Column(String(10), comment="차량 종류 코드")
    vhcle_knd_nm = Column(String(50), comment="차량 종류명")

    ntsl_pc = Column(Integer, comment="판매 가격")

    setle_mthd_cd = Column(String(10), comment="결제 방식 코드")
    setle_mthd_nm = Column(String(50), comment="결제 방식명")

    use_posbl_dotw = Column(String(20), comment="이용 가능 요일 코드")

    usebhr_hr_mon = Column(Time, nullable=True, comment="월요일 시작 시간")
    useehr_hr_mon = Column(Time, nullable=True, comment="월요일 종료 시간")

    usebhr_hr_tues = Column(Time, nullable=True, comment="화요일 시작 시간")
    useehr_hr_tues = Column(Time, nullable=True, comment="화요일 종료 시간")

    usebhr_hr_wed = Column(Time, nullable=True, comment="수요일 시작 시간")
    useehr_hr_wed = Column(Time, nullable=True, comment="수요일 종료 시간")

    usebhr_hr_thur = Column(Time, nullable=True, comment="목요일 시작 시간")
    useehr_hr_thur = Column(Time, nullable=True, comment="목요일 종료 시간")

    usebhr_hr_fri = Column(Time, nullable=True, comment="금요일 시작 시간")
    useehr_hr_fri = Column(Time, nullable=True, comment="금요일 종료 시간")

    usebhr_hr_sat = Column(Time, nullable=True, comment="토요일 시작 시간")
    useehr_hr_sat = Column(Time, nullable=True, comment="토요일 종료 시간")

    usebhr_hr_sun = Column(Time, nullable=True, comment="일요일 시작 시간")
    useehr_hr_sun = Column(Time, nullable=True, comment="일요일 종료 시간")

    usebhr_hr_hldy = Column(Time, nullable=True, comment="공휴일 시작 시간")
    useehr_hr_hldy = Column(Time, nullable=True, comment="공휴일 종료 시간")

    rest_bgng_hr = Column(Time, nullable=True, comment="휴게 시작 시간")
    rest_end_hr = Column(Time, nullable=True, comment="휴게 종료 시간")

    rsvt_posbl_yn = Column(CHAR(1), comment="예약 가능 여부 Y/N")

    lon = Column(DECIMAL(17, 14), comment="경도")
    let = Column(DECIMAL(17, 14), comment="위도")

    oper_yn = Column(CHAR(1), comment="운영 여부 Y/N")
    del_at = Column(CHAR(1), default="0", comment="삭제 여부")

    last_mdfcn_dt = Column(DateTime(timezone=True), nullable=True, comment="최종 수정 일시")
    timestamp = Column(DateTime(timezone=True), nullable=True, comment="데이터 수집 또는 갱신 일시")

    rltm_info_yn = Column(CHAR(1), comment="실시간 정보 제공 여부 Y/N")

    status_list = relationship(
        "HydrogenStationStatus",
        back_populates="station",
        cascade="all, delete-orphan",
    )

    facilities_list = relationship(
        "HydrogenStationAdditionalInfo",
        back_populates="station",
        cascade="all, delete-orphan",
    )