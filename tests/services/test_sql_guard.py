import pytest

from app.services.sql_guard import UnsafeSqlError, validate_station_sql

_VALID = "SELECT chrstn_mno, chrstn_nm, lon, let FROM hydrogen_stations WHERE oper_yn='Y' AND del_at='0'"


def test_allows_single_select():
    assert validate_station_sql(_VALID) == _VALID


def test_strips_trailing_semicolon():
    assert validate_station_sql(_VALID + ";") == _VALID


def test_allows_leading_parenthesis_select():
    sql = "(SELECT chrstn_mno FROM hydrogen_stations)"
    assert validate_station_sql(sql) == sql


def test_allows_union_select():
    sql = "SELECT chrstn_mno FROM hydrogen_stations UNION SELECT chrstn_mno FROM hydrogen_stations"
    assert validate_station_sql(sql) == sql


@pytest.mark.parametrize("sql", ["", "   ", None])
def test_rejects_empty(sql):
    with pytest.raises(UnsafeSqlError):
        validate_station_sql(sql)


def test_rejects_multiple_statements():
    with pytest.raises(UnsafeSqlError):
        validate_station_sql("SELECT 1; DELETE FROM hydrogen_stations")


def test_rejects_mid_statement_semicolon():
    with pytest.raises(UnsafeSqlError):
        validate_station_sql("SELECT 1; SELECT 2;")


@pytest.mark.parametrize(
    "sql",
    [
        "DROP TABLE hydrogen_stations",
        "UPDATE hydrogen_stations SET oper_yn='N'",
        "DELETE FROM hydrogen_stations",
        "INSERT INTO hydrogen_stations VALUES (1)",
        "ALTER TABLE hydrogen_stations ADD COLUMN x INT",
        "TRUNCATE hydrogen_stations",
    ],
)
def test_rejects_non_select_statements(sql):
    with pytest.raises(UnsafeSqlError):
        validate_station_sql(sql)


def test_rejects_select_into():
    with pytest.raises(UnsafeSqlError):
        validate_station_sql("SELECT * INTO backup FROM hydrogen_stations")


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT chrstn_mno FROM hydrogen_stations -- drop everything",
        "SELECT chrstn_mno FROM hydrogen_stations /* comment */",
        "SELECT chrstn_mno FROM hydrogen_stations # hash",
    ],
)
def test_rejects_sql_comments(sql):
    with pytest.raises(UnsafeSqlError):
        validate_station_sql(sql)


def test_rejects_cte_not_starting_with_select():
    # CTE(WITH ...)는 SELECT로 시작하지 않으므로 차단된다(설계상 의도).
    with pytest.raises(UnsafeSqlError):
        validate_station_sql("WITH x AS (SELECT 1) SELECT * FROM x")


def test_keyword_match_is_word_boundary():
    # 'updated_at' 같은 컬럼명은 UPDATE 키워드로 오탐되지 않아야 한다.
    sql = "SELECT chrstn_mno, last_updated_at FROM hydrogen_stations"
    assert validate_station_sql(sql) == sql
