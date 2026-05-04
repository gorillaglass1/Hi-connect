def test_create_station_success(client):
    payload = {
        "name": "Gangnam Station",
        "address": "Seoul",
        "latitude": 37.5,
        "longitude": 127.0,
        "contact_number": "02-111-2222",
        "start_time": "08:00:00",
        "end_time": "20:00:00",
        "total_chargers": 4,
        "payment_supported": "CARD",
    }
    res = client.post("/hydrogen-stations", json=payload)

    assert res.status_code == 201
    assert res.json()["name"] == payload["name"]


def test_list_stations_filter_by_name(client):
    client.post(
        "/hydrogen-stations",
        json={
            "name": "OnlyMe",
            "address": "Busan",
            "latitude": 35.1,
            "longitude": 129.0,
            "total_chargers": 2,
        },
    )

    res = client.get("/hydrogen-stations", params={"name": "OnlyMe"})
    assert res.status_code == 200
    assert len(res.json()) >= 1
