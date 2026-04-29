def test_signup_user_success(client):
    payload = {
        "name": "Seo",
        "phone": "010-1111-2222",
        "email": "seo@example.com",
    }

    response = client.post("/user/signup", json=payload)

    assert response.status_code == 200
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
    assert first_response.status_code == 200

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
