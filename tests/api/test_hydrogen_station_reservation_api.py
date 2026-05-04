from datetime import datetime, timedelta


def test_create_reservation_success(client):
    user = client.post(
        "/user/signup",
        json={"name": "R1", "phone": "010-2", "email": "r1@example.com"},
    ).json()
    station = client.post(
        "/hydrogen-stations",
        json={
            "name": "R-Station",
            "address": "Seoul",
            "latitude": 37.5,
            "longitude": 127.0,
            "total_chargers": 2,
        },
    ).json()
    charger = client.post(
        "/hydrogen-chargers",
        json={
            "hydrogen_station_id": station["hydrogen_station_id"],
            "charger_status": "충분",
            "pressure_type": "700bar",
        },
    ).json()

    now = datetime.now()
    res = client.post(
        "/hydrogen-station-reservations",
        json={
            "hydrogen_charger_id": charger["hydrogen_charger_id"],
            "hydrogen_station_id": station["hydrogen_station_id"],
            "reservation_status": "RESERVED",
            "user_id": user["user_id"],
            "reservation_time": now.isoformat(),
            "expire_time": (now + timedelta(minutes=20)).isoformat(),
        },
    )

    assert res.status_code == 200


def test_create_reservation_invalid_time_returns_400(client):
    now = datetime.now()
    res = client.post(
        "/hydrogen-station-reservations",
        json={
            "hydrogen_charger_id": 1,
            "hydrogen_station_id": 1,
            "reservation_status": "RESERVED",
            "user_id": 1,
            "reservation_time": now.isoformat(),
            "expire_time": (now - timedelta(minutes=1)).isoformat(),
        },
    )
    assert res.status_code == 400
