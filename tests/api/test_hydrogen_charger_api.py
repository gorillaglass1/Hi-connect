def test_create_charger_success(client):
    station = client.post(
        "/hydrogen-stations",
        json={
            "name": "S1",
            "address": "Seoul",
            "latitude": 37.5,
            "longitude": 127.0,
            "total_chargers": 2,
        },
    ).json()

    payload = {
        "hydrogen_station_id": station["hydrogen_station_id"],
        "charger_status": "충분",
        "pressure_type": "700bar",
        "charger_type": "FAST",
        "hydrogen_pressure_bar": 700,
    }
    res = client.post("/hydrogen-chargers", json=payload)

    assert res.status_code == 201
    assert res.json()["pressure_type"] == "700bar"


def test_create_charger_negative_pressure_returns_400(client):
    station = client.post(
        "/hydrogen-stations",
        json={
            "name": "S2",
            "address": "Seoul",
            "latitude": 37.5,
            "longitude": 127.0,
            "total_chargers": 2,
        },
    ).json()

    res = client.post(
        "/hydrogen-chargers",
        json={
            "hydrogen_station_id": station["hydrogen_station_id"],
            "charger_status": "충분",
            "pressure_type": "700bar",
            "hydrogen_pressure_bar": -1,
        },
    )
    assert res.status_code == 400
