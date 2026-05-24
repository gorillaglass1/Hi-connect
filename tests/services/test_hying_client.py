import httpx
import pytest

from app.services.hying_client import HyingClient


class FakeAsyncClient:
    request_params = None
    request_headers = None

    def __init__(self, base_url=None, timeout=None):
        self.base_url = base_url
        self.timeout = timeout

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, endpoint, params=None, headers=None):
        self.__class__.request_params = params
        self.__class__.request_headers = headers
        return httpx.Response(
            200,
            json=[{"chrstn_mno": "ST-001"}],
            request=httpx.Request("GET", f"https://example.com{endpoint}"),
        )


@pytest.mark.asyncio
async def test_hying_client_sends_api_key_as_authorization_header(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)
    monkeypatch.setenv("HYING_STATIONS_ENDPOINT", "/api/chrstnList/operationInfo")

    client = HyingClient(base_url="https://example.com", api_key="test-key")

    result = await client.fetch_stations({"pageNo": 1})

    assert result == [{"chrstn_mno": "ST-001"}]
    assert FakeAsyncClient.request_params == {"pageNo": 1}
    assert FakeAsyncClient.request_headers["Authorization"] == "test-key"
    assert "serviceKey" not in FakeAsyncClient.request_params
