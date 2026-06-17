import logging
import re
from dataclasses import dataclass, field

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.hydrogen_station import HydrogenStation
from app.models.hydrogen_station_facilities import HydrogenStationAdditionalInfo
from app.models.hydrogen_station_status import HydrogenStationStatus

logger = logging.getLogger("rule_based_station_filter_service")


# 광역시/도 등 주소에 흔히 등장하는 지역 키워드. 질의에 그대로 포함되면 주소 LIKE 조건으로 사용한다.
REGION_KEYWORDS = [
    "서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종",
    "경기", "강원", "충북", "충청북도", "충남", "충청남도",
    "전북", "전라북도", "전남", "전라남도",
    "경북", "경상북도", "경남", "경상남도", "제주",
]

# "수원시", "남동구", "달성군" 처럼 행정구역 접미사로 끝나는 지명을 추가로 인식한다.
REGION_SUFFIX_PATTERN = re.compile(r"([가-힣]{2,4}(?:특별시|광역시|특별자치시|특별자치도|시|군|구))")

# 부대시설 키워드 -> 충전소 부대시설명(adi_info_se_nm) LIKE 토큰.
FACILITY_KEYWORDS = {
    "세차": "세차",
    "편의점": "편의점",
    "카페": "카페",
    "휴게": "휴게",
    "화장실": "화장실",
    "식당": "식당",
    "정비": "정비",
    "주차": "주차",
}

PRICE_LIMIT_PATTERN = re.compile(r"([\d,]{3,})\s*원?\s*(?:이하|이내|미만|아래|under)")


@dataclass
class StationFilterConditions:
    """nl_query에서 규칙 기반으로 추출한 충전소 후보 필터 조건."""

    regions: list[str] = field(default_factory=list)
    max_price: int | None = None
    facilities: list[str] = field(default_factory=list)
    require_no_wait: bool = False
    require_short_wait: bool = False
    require_open: bool = False
    require_operating: bool = False
    require_reservation: bool = False
    require_realtime: bool = False

    def has_any(self) -> bool:
        return any(
            [
                self.regions,
                self.max_price is not None,
                self.facilities,
                self.require_no_wait,
                self.require_short_wait,
                self.require_open,
                self.require_operating,
                self.require_reservation,
                self.require_realtime,
            ]
        )


class RuleBasedStationFilterService:
    """자연어 질의를 규칙 기반으로 해석해 후보 충전소 ID 목록을 만든다.

    Text-to-SQL(LLM)을 대체하며, 외부 API 호출 없이 결정적으로 동작한다.
    """

    SHORT_WAIT_THRESHOLD = 3

    def __init__(self, db: AsyncSession):
        self.db = db

    def parse(self, nl_query: str) -> StationFilterConditions:
        query = nl_query.strip()
        conditions = StationFilterConditions()

        # 1. 지역/주소
        regions: list[str] = []
        for keyword in REGION_KEYWORDS:
            if keyword in query:
                regions.append(keyword)
        for match in REGION_SUFFIX_PATTERN.findall(query):
            regions.append(match)
        # 중복 제거(입력 순서 유지) 및 다른 지역명의 접두사인 경우 제거.
        deduped: list[str] = []
        for region in regions:
            if region not in deduped:
                deduped.append(region)
        conditions.regions = [
            region
            for region in deduped
            if not any(region != other and region in other for other in deduped)
        ]

        # 2. 가격 상한
        price_match = PRICE_LIMIT_PATTERN.search(query)
        if price_match:
            conditions.max_price = int(price_match.group(1).replace(",", ""))

        # 3. 부대시설
        for keyword, token in FACILITY_KEYWORDS.items():
            if keyword in query and token not in conditions.facilities:
                conditions.facilities.append(token)

        # 4. 대기 차량
        if "대기" in query:
            if any(word in query for word in ("없는", "없이", "없음", "제로", "0대")):
                conditions.require_no_wait = True
            elif any(word in query for word in ("적은", "짧은", "적게", "여유")):
                conditions.require_short_wait = True

        # 5. 운영/영업 상태 및 기타 플래그
        if "영업중" in query or "영업 중" in query:
            conditions.require_open = True
        if "운영중" in query or "운영 중" in query:
            conditions.require_operating = True
        if "예약" in query and "가능" in query:
            conditions.require_reservation = True
        if "실시간" in query:
            conditions.require_realtime = True

        return conditions

    def _latest_status_subquery(self):
        return (
            select(HydrogenStationStatus.status_id)
            .where(HydrogenStationStatus.chrstn_mno == HydrogenStation.chrstn_mno)
            .order_by(
                HydrogenStationStatus.last_mdfcn_dt.desc().nullslast(),
                HydrogenStationStatus.status_id.desc(),
            )
            .limit(1)
            .correlate(HydrogenStation)
            .scalar_subquery()
        )

    def _build_query(self, conditions: StationFilterConditions):
        latest_status_id_subquery = self._latest_status_subquery()
        query = (
            select(HydrogenStation.chrstn_mno)
            .outerjoin(
                HydrogenStationStatus,
                HydrogenStationStatus.status_id == latest_status_id_subquery,
            )
            .where(HydrogenStation.oper_yn == "Y")
            .where(HydrogenStation.del_at == "0")
        )

        if conditions.regions:
            region_clauses = []
            for region in conditions.regions:
                pattern = f"%{region}%"
                region_clauses.append(HydrogenStation.road_nm_addr.ilike(pattern))
                region_clauses.append(HydrogenStation.lotno_addr.ilike(pattern))
            query = query.where(or_(*region_clauses))

        if conditions.max_price is not None:
            query = query.where(HydrogenStation.ntsl_pc <= conditions.max_price)

        for facility in conditions.facilities:
            query = query.where(
                HydrogenStation.facilities_list.any(
                    and_(
                        HydrogenStationAdditionalInfo.adi_info_se_nm.ilike(f"%{facility}%"),
                        HydrogenStationAdditionalInfo.del_at == "0",
                    )
                )
            )

        if conditions.require_no_wait:
            query = query.where(HydrogenStationStatus.wait_vhcle_alge == 0)
        elif conditions.require_short_wait:
            query = query.where(
                HydrogenStationStatus.wait_vhcle_alge <= self.SHORT_WAIT_THRESHOLD
            )

        if conditions.require_open:
            query = query.where(HydrogenStationStatus.pos_sttus_nm.ilike("%영업%"))
        if conditions.require_operating:
            query = query.where(HydrogenStationStatus.oper_sttus_nm.ilike("%운영%"))
        if conditions.require_reservation:
            query = query.where(HydrogenStation.rsvt_posbl_yn == "Y")
        if conditions.require_realtime:
            query = query.where(HydrogenStation.rltm_info_yn == "Y")

        return query

    async def execute_search(self, natural_language_query: str) -> list[str] | None:
        """질의를 해석해 매칭되는 충전소 관리번호 목록을 반환한다.

        해석 가능한 조건이 하나도 없으면 None을 반환해 전체 충전소 채점으로 폴백하게 한다.
        조건이 있지만 매칭이 없으면 빈 리스트([])를 반환한다.
        """
        conditions = self.parse(natural_language_query)
        if not conditions.has_any():
            logger.info(
                "Rule-based filter found no recognizable conditions in query: %s",
                natural_language_query,
            )
            return None

        logger.info("Rule-based filter conditions: %s", conditions)
        query = self._build_query(conditions)

        try:
            result = await self.db.execute(query)
            matching_mno_list = [row[0] for row in result.all() if row[0] is not None]
            return matching_mno_list
        except Exception as exc:  # pragma: no cover - defensive
            await self.db.rollback()
            logger.error("Rule-based filter query failed: %s", exc)
            return None
