def test_create_user_initializes_preferences(client):
    res = client.post(
        "/users",
        json={
            "name": "API 신규 사용자",
            "phone": "010-2222-3333",
            "email": "api-new-user@example.com",
        },
    )

    assert res.status_code == 201
    body = res.json()
    assert body["user_id"] is not None
    assert body["name"] == "API 신규 사용자"
    assert body["preferences"]["weight_price"] == "1.00"
    assert body["preferences"]["safety_margin"] == "1.10"


def test_create_user_duplicate_email_returns_409(client):
    payload = {
        "name": "API 중복 사용자",
        "phone": "010-2222-4444",
        "email": "api-duplicate-user@example.com",
    }

    first_res = client.post("/users", json=payload)
    second_res = client.post("/users", json=payload)

    assert first_res.status_code == 201
    assert second_res.status_code == 409


def test_update_user_preferences(client):
    create_res = client.post(
        "/users",
        json={
            "name": "API 가중치 사용자",
            "phone": "010-2222-5555",
            "email": "api-pref-user@example.com",
        },
    )
    user_id = create_res.json()["user_id"]

    update_res = client.put(
        f"/users/{user_id}/preferences",
        json={
            "weight_price": "2.2",
            "weight_waiting_time": "1.5",
            "weight_distance": "0.8",
            "weight_facilities": "0.4",
            "safety_margin": "1.15",
        },
    )

    assert update_res.status_code == 200
    body = update_res.json()
    assert body["user_id"] == user_id
    assert body["weight_price"] == "2.20"
    assert body["safety_margin"] == "1.15"
