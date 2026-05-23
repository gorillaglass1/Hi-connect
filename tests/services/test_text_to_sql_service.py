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
