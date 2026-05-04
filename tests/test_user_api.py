def test_signup_user_success(client):
    payload = {
        "name": "Seo",
        "phone": "010-1111-2222",
        "email": "seo@example.com",
    }

    response = client.post("/user/signup", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == payload["name"]
    assert body["phone"] == payload["phone"]
    assert body["email"] == payload["email"]
    assert isinstance(body["user_id"], int)


def test_signup_user_duplicate_email_returns_409(client):
    payload = {
        "name": "Seo",
        "phone": "010-1111-2222",
        "email": "seo-dup@example.com",
    }

    first_response = client.post("/user/signup", json=payload)
    assert first_response.status_code == 201

    second_response = client.post("/user/signup", json=payload)
    assert second_response.status_code == 409
    assert second_response.json()["detail"] == "Email already exists"


def test_signup_user_invalid_email_returns_422(client):
    payload = {
        "name": "Kim",
        "phone": "010-3333-4444",
        "email": "not-an-email",
    }

    response = client.post("/user/signup", json=payload)

    assert response.status_code == 422


def test_update_user_with_email_returns_422(client):
    create_payload = {
        "name": "Seo",
        "phone": "010-1111-2222",
        "email": "seo-update-block@example.com",
    }
    create_response = client.post("/user/signup", json=create_payload)
    assert create_response.status_code == 201
    user_id = create_response.json()["user_id"]

    response = client.patch(
        f"/user/update/{user_id}",
        json={"email": "new-email@example.com"},
    )
    assert response.status_code == 422
