def test_list_endpoints_reject_invalid_pagination(client):
    endpoints = [
        "/hydrogen-stations",
        "/hydrogen-stations/details",
        "/hydrogen-station-status",
        "/hydrogen-station-facilities",
        "/charging-logs",
        "/recommendation-histories",
    ]

    for endpoint in endpoints:
        response = client.get(endpoint, params={"limit": 0})
        assert response.status_code == 422, endpoint

        response = client.get(endpoint, params={"offset": -1})
        assert response.status_code == 422, endpoint


def test_hydrogen_station_details_rejects_unknown_sort_field(client):
    response = client.get(
        "/hydrogen-stations/details",
        params={"sort_by": "unknown"},
    )

    assert response.status_code == 422


def test_hydrogen_station_details_rejects_unknown_sort_order(client):
    response = client.get(
        "/hydrogen-stations/details",
        params={"sort_order": "sideways"},
    )

    assert response.status_code == 422


def test_sync_hydrogen_stations_passes_optional_paging_params(client, monkeypatch):
    captured = {}

    async def fake_sync_from_hying(self, params=None):
        captured["params"] = params
        return {"fetched": 2, "saved": 2}

    monkeypatch.setattr(
        "app.services.hydrogen_station_service.HydrogenStationService.sync_from_hying",
        fake_sync_from_hying,
    )

    response = client.post(
        "/hydrogen-stations/sync",
        params={"page_no": 3, "num_of_rows": 50},
    )

    assert response.status_code == 200
    assert response.json() == {"fetched": 2, "saved": 2}
    assert captured["params"] == {"pageNo": 3, "numOfRows": 50}


def test_sync_hydrogen_station_status_passes_optional_paging_params(
    client,
    monkeypatch,
):
    captured = {}

    async def fake_sync_from_hying(self, params=None):
        captured["params"] = params
        return {"fetched": 5, "saved": 4, "skipped": 1}

    monkeypatch.setattr(
        "app.services.hydrogen_station_status_service."
        "HydrogenStationStatusService.sync_from_hying",
        fake_sync_from_hying,
    )

    response = client.post(
        "/hydrogen-station-status/sync",
        params={"page_no": 2, "num_of_rows": 25},
    )

    assert response.status_code == 200
    assert response.json() == {"fetched": 5, "saved": 4, "skipped": 1}
    assert captured["params"] == {"pageNo": 2, "numOfRows": 25}


def test_sync_hydrogen_station_facilities_uses_service(client, monkeypatch):
    async def fake_sync_from_hying(self):
        return {"fetched": 3, "saved": 2, "skipped": 1}

    monkeypatch.setattr(
        "app.services.hydrogen_station_facilities_service."
        "HydrogenStationFacilitiesService.sync_from_hying",
        fake_sync_from_hying,
    )

    response = client.post("/hydrogen-station-facilities/sync")

    assert response.status_code == 200
    assert response.json() == {"fetched": 3, "saved": 2, "skipped": 1}


def test_sync_endpoints_reject_invalid_paging_params(client):
    endpoints = [
        "/hydrogen-stations/sync",
        "/hydrogen-station-status/sync",
    ]

    for endpoint in endpoints:
        response = client.post(endpoint, params={"page_no": 0})
        assert response.status_code == 422, endpoint

        response = client.post(endpoint, params={"num_of_rows": 1001})
        assert response.status_code == 422, endpoint
