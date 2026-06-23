"""LLM이 생성한 충전소 조회 SQL의 안전성 검증.

대시보드 통합 인사이트는 LLM이 `station_sql`(단일 SELECT 문)을 만들어 보낸다.
이 모듈은 그 문자열을 실행하기 전에 "읽기 전용 단일 SELECT"인지 검증한다.

설계 메모:
- 기존 자연어 후보 필터(RuleBasedStationFilterService)는 SQLAlchemy 쿼리를
  결정적으로 조립하므로 원시 SQL 문자열 검증기가 따로 없었다. 대시보드는
  LLM이 만든 원시 SQL을 실행해야 하므로 이 전용 검증기를 새로 둔다.
"""

import re

# SELECT를 제외한 모든 DML/DDL/권한 변경 키워드는 금지한다.
_FORBIDDEN_KEYWORDS = (
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE",
    "REPLACE", "MERGE", "GRANT", "REVOKE", "EXEC", "EXECUTE", "CALL",
    "ATTACH", "DETACH", "PRAGMA", "VACUUM", "COPY", "INTO",
)

# 주석을 이용한 우회를 막기 위해 SQL 주석 토큰도 금지한다.
_COMMENT_PATTERN = re.compile(r"(--|/\*|\*/|#)")

# 키워드는 단어 경계 기준으로만 검사한다. (예: 컬럼명에 'created' 같은 단어가 와도 오탐 방지)
_FORBIDDEN_PATTERN = re.compile(
    r"\b(" + "|".join(_FORBIDDEN_KEYWORDS) + r")\b", re.IGNORECASE
)


class UnsafeSqlError(ValueError):
    """검증을 통과하지 못한(안전하지 않은) SQL."""


def validate_station_sql(sql: str | None) -> str:
    """원시 SQL이 안전한 단일 SELECT인지 검증하고 정리된 문자열을 반환한다.

    규칙:
    - 단일 SELECT 문만 허용 (세미콜론 1개 이하).
    - INSERT/UPDATE/DELETE/DROP/ALTER 등 변경 계열 키워드 금지.
    - SQL 주석(--, /* */, #) 금지.

    위반 시 :class:`UnsafeSqlError`를 발생시킨다. 호출 측은 이를 잡아
    백엔드 기본 조회로 폴백해야 한다.
    """
    if not sql or not sql.strip():
        raise UnsafeSqlError("빈 SQL은 허용되지 않습니다.")

    cleaned = sql.strip()

    # 세미콜론은 1개 이하만 허용하고, 있더라도 끝의 종결자만 인정한다.
    if cleaned.count(";") > 1:
        raise UnsafeSqlError("복수의 SQL 문(세미콜론 2개 이상)은 허용되지 않습니다.")
    cleaned = cleaned.rstrip(";").strip()
    if ";" in cleaned:
        raise UnsafeSqlError("문장 중간의 세미콜론은 허용되지 않습니다.")

    if _COMMENT_PATTERN.search(cleaned):
        raise UnsafeSqlError("SQL 주석은 허용되지 않습니다.")

    if not re.match(r"^\(?\s*SELECT\b", cleaned, re.IGNORECASE):
        raise UnsafeSqlError("SELECT 문만 허용됩니다.")

    forbidden = _FORBIDDEN_PATTERN.search(cleaned)
    if forbidden:
        raise UnsafeSqlError(f"금지된 키워드가 포함되어 있습니다: {forbidden.group(1)}")

    return cleaned
