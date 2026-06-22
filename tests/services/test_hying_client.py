import httpx
import pytest
from fastapi import HTTPException

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


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        ([{"chrstn_mno": "A"}, "skip", {"chrstn_mno": "B"}], [{"chrstn_mno": "A"}, {"chrstn_mno": "B"}]),
        ({"chrstn_mno": "ROOT"}, [{"chrstn_mno": "ROOT"}]),
        ({"items": [{"chrstn_mno": "ITEM"}]}, [{"chrstn_mno": "ITEM"}]),
        ({"response": {"body": {"items": [{"chrstn_mno": "NESTED"}]}}}, [{"chrstn_mno": "NESTED"}]),
        ("not-json-object", []),
        ({"items": []}, []),
    ],
)
def test_hying_client_extract_items_handles_supported_payload_shapes(payload, expected):
    client = HyingClient(base_url="https://example.com")

    assert client._extract_items(payload) == expected


@pytest.mark.asyncio
async def test_hying_client_requires_base_url_and_endpoint(monkeypatch):
    monkeypatch.delenv("HYING_STATIONS_ENDPOINT", raising=False)
    client = HyingClient(base_url="", api_key=None)

    with pytest.raises(HTTPException) as exc_info:
        await client.fetch_stations()

    assert exc_info.value.status_code == 503


@pytest.mark.asyncio
async def test_hying_facilities_request_ignores_params(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)
    monkeypatch.setenv("HYING_STATION_FACILITIES_ENDPOINT", "/facilities")
    FakeAsyncClient.request_params = {"stale": True}

    client = HyingClient(base_url="https://example.com", api_key=None)
    result = await client.fetch_station_facilities({"pageNo": 99})

    assert result == [{"chrstn_mno": "ST-001"}]
    assert FakeAsyncClient.request_params == {}
