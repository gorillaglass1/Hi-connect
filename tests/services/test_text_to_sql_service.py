import pytest

from app.services.text_to_sql_service import TextToSqlService


class FailingDb:
    def __init__(self):
        self.rollback_called = False

    async def execute(self, _query):
        raise RuntimeError("bad generated sql")

    async def rollback(self):
        self.rollback_called = True


@pytest.mark.asyncio
async def test_execute_semantic_search_rolls_back_failed_sql_execution(monkeypatch):
    db = FailingDb()
    service = TextToSqlService(db)

    async def fake_translate_to_sql(_query: str):
        return "SELECT DISTINCT hs.chrstn_mno FROM hydrogen_stations hs"

    monkeypatch.setattr(service, "translate_to_sql", fake_translate_to_sql)

    result = await service.execute_semantic_search("대기 차량 적은 충전소")

    assert result is None
    assert db.rollback_called is True


def test_clean_sql_output_removes_markdown_fences():
    service = TextToSqlService(db=None)

    cleaned = service._clean_sql_output(
        """
        ```sql
        SELECT DISTINCT hs.chrstn_mno FROM hydrogen_stations hs;
        ```
        """
    )

    assert cleaned == "SELECT DISTINCT hs.chrstn_mno FROM hydrogen_stations hs;"


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT DISTINCT chrstn_mno FROM hydrogen_stations",
        " select hs.chrstn_mno from hydrogen_stations hs ",
    ],
)
def test_is_safe_select_query_accepts_select_only_queries(sql):
    service = TextToSqlService(db=None)

    assert service._is_safe_select_query(sql) is True


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM hydrogen_stations",
        "SELECT * FROM hydrogen_stations UNION SELECT * FROM users",
        "SELECT * INTO copied_table FROM hydrogen_stations",
        "DROP TABLE hydrogen_stations",
        "UPDATE hydrogen_stations SET oper_yn = 'N'",
    ],
)
def test_is_safe_select_query_rejects_mutating_or_expansive_keywords(sql):
    service = TextToSqlService(db=None)

    assert service._is_safe_select_query(sql) is False


@pytest.mark.asyncio
async def test_execute_semantic_search_returns_station_ids(monkeypatch):
    class FakeResult:
        def fetchall(self):
            return [("TXT-ST-001",), (None,), ("TXT-ST-002",)]

    class FakeDb:
        async def execute(self, _query):
            return FakeResult()

    service = TextToSqlService(FakeDb())

    async def fake_translate_to_sql(_query: str):
        return "SELECT DISTINCT hs.chrstn_mno FROM hydrogen_stations hs"

    monkeypatch.setattr(service, "translate_to_sql", fake_translate_to_sql)

    result = await service.execute_semantic_search("인천 충전소")

    assert result == ["TXT-ST-001", "TXT-ST-002"]


@pytest.mark.asyncio
async def test_translate_to_sql_returns_none_without_client(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    service = TextToSqlService(db=None)
    service.client = None

    result = await service.translate_to_sql("인천 충전소")

    assert result is None
