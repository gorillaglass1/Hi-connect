def test_promo_page_serves_brochure_html(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "HY-CONNECT" in response.text
    assert "/static/hyconnect-hero.png" in response.text
    assert "대시보드 실행" in response.text


def test_dashboard_page_serves_learning_test_ui(client):
    response = client.get("/dashboard")

    assert response.status_code == 200
    assert "recommendations/personalized/delivery-payloads" in response.text
    assert "preferences/learn" in response.text
    assert "경로안내" in response.text
    assert "차량 전송용 추천 JSON" not in response.text


def test_promo_hero_asset_is_served(client):
    response = client.get("/static/hyconnect-hero.png")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert len(response.content) > 0
