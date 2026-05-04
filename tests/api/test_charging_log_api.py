from datetime import datetime, timedelta


def test_create_charging_log_success(client):
    user = client.post(
        "/user/signup",
        json={"name": "C1", "phone": "010-3", "email": "c1@example.com"},
    ).json()
    station = client.post(
        "/hydrogen-stations",
        json={
            "name": "C-Station",
            "address": "Seoul",
            "latitude": 37.5,
            "longitude": 127.0,
            "total_chargers": 2,
        },
    ).json()
    vehicle = client.post(
        "/vehicles",
        json={
            "user_id": user["user_id"],
            "vehicle_number": "11가1111",
            "model": "NEXO",
            "vehicle_type": "SUV",
            "fuel_type": "hydrogen",
            "tank_capacity": 6.0,
        },
    ).json()

    now = datetime.now()
    res = client.post(
        "/charging-logs",
        json={
            "user_id": user["user_id"],
            "hydrogen_station_id": station["hydrogen_station_id"],
            "vehicle_id": vehicle["vehicle_id"],
            "start_time": now.isoformat(),
            "end_time": (now + timedelta(minutes=30)).isoformat(),
            "charged_amount": 3.2,
        },
    )

    assert res.status_code == 201


def test_create_charging_log_invalid_time_returns_400(client):
    now = datetime.now()
    res = client.post(
        "/charging-logs",
        json={
            "user_id": 1,
            "hydrogen_station_id": 1,
            "vehicle_id": 1,
            "start_time": now.isoformat(),
            "end_time": (now - timedelta(minutes=1)).isoformat(),
        },
    )
    assert res.status_code == 400
