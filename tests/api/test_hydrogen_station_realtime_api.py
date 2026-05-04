def test_upsert_station_realtime_success(client):
    station = client.post(
        "/hydrogen-stations",
        json={
            "name": "RS1",
            "address": "Seoul",
            "latitude": 37.5,
            "longitude": 127.0,
            "total_chargers": 2,
        },
    ).json()

    res = client.post(
        "/hydrogen-station-realtime",
        json={
            "hydrogen_station_id": station["hydrogen_station_id"],
            "available_chargers": 1,
            "in_use_chargers": 1,
            "queue_count": 2,
            "station_status": "busy",
        },
    )

    assert res.status_code == 201
    assert res.json()["hydrogen_station_id"] == station["hydrogen_station_id"]


def test_list_station_realtime_success(client):
    res = client.get("/hydrogen-station-realtime")
    assert res.status_code == 200
    assert isinstance(res.json(), list)
