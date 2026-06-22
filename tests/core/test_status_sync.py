from app.core import status_sync


def test_status_sync_is_not_configured_without_endpoint(monkeypatch):
    monkeypatch.setenv("HYING_STATUS_SYNC_ENABLED", "true")
    monkeypatch.setenv("HYING_API_BASE_URL", "https://www.h2nbiz.or.kr")
    monkeypatch.delenv("HYING_STATION_STATUS_ENDPOINT", raising=False)

    assert status_sync.status_sync_is_configured() is False


def test_status_sync_is_configured_with_base_url_and_endpoint(monkeypatch):
    monkeypatch.setenv("HYING_STATUS_SYNC_ENABLED", "true")
    monkeypatch.setenv("HYING_API_BASE_URL", "https://www.h2nbiz.or.kr")
    monkeypatch.setenv("HYING_STATION_STATUS_ENDPOINT", "/api/status")

    assert status_sync.status_sync_is_configured() is True


def test_status_sync_interval_defaults_to_five_minutes(monkeypatch):
    monkeypatch.delenv("HYING_STATUS_SYNC_INTERVAL_SECONDS", raising=False)

    assert status_sync.status_sync_interval_seconds() == 300
