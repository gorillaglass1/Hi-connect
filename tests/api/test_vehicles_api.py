from app.repositories.user_repo import create_user


def test_create_vehicle_success(client):
    user = client.post(
        "/user/signup",
        json={"name": "U1", "phone": "010-1", "email": "u1@example.com"},
    ).json()

    payload = {
        "user_id": user["user_id"],
        "vehicle_number": "99가9999",
        "model": "NEXO",
        "vehicle_type": "SUV",
        "fuel_type": "hydrogen",
        "tank_capacity": 6.3,
        "avg_efficiency": 90.5,
    }
    res = client.post("/vehicles", json=payload)

    assert res.status_code == 201
    assert res.json()["vehicle_number"] == payload["vehicle_number"]


def test_get_vehicle_not_found_returns_404(client):
    res = client.get("/vehicles/999999")
    assert res.status_code == 404
    assert res.json()["detail"] == "Vehicle not found"
