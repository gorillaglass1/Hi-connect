def test_create_user_success(client):
    # 1. 요청 데이터 준비
    payload = {
        "name": "test_name",
        "phone": "test_phone",
        "email": "test@test.com",
    }


    res = client.post("/user", json=payload)


    assert res.status_code == 201

    data = res.json()
    assert data["name"] == payload["name"]
    assert isinstance(data["user_id"], int)
    assert data["user_id"] > 0
