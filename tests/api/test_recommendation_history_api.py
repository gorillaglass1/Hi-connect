def test_create_recommendation_history_success(client):
    user = client.post(
        "/user/signup",
        json={"name": "H1", "phone": "010-4", "email": "h1@example.com"},
    ).json()
    station = client.post(
        "/hydrogen-stations",
        json={
            "name": "H-Station",
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
            "vehicle_number": "22가2222",
            "model": "NEXO",
            "vehicle_type": "SUV",
            "fuel_type": "hydrogen",
            "tank_capacity": 6.0,
        },
    ).json()

    res = client.post(
        "/recommendation-histories",
        json={
            "user_id": user["user_id"],
            "vehicle_id": vehicle["vehicle_id"],
            "hydrogen_station_id": station["hydrogen_station_id"],
            "recommendation_score": 91.2,
            "selected": True,
            "recommendation_type": "distance",
        },
    )

    assert res.status_code == 200


def test_list_recommendation_histories_success(client):
    res = client.get("/recommendation-histories")
    assert res.status_code == 200
    assert isinstance(res.json(), list)
