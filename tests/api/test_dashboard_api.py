from app.services import dashboard_service as ds_module


def _seed_operating_station(client):
    client.post(
        "/hydrogen-stations",
        json={
            "chrstn_mno": "DASH-API-001",
            "chrstn_nm": "대시보드 API 충전소",
            "lon": 126.9785,
            "let": 37.5670,
            "oper_yn": "Y",
            "del_at": "0",
        },
    )


def test_dashboard_insights_returns_full_payload(client):
    ds_module._cache.clear()
    _seed_operating_station(client)

    res = client.get(
        "/dashboard/insights",
        params={"lat": 37.5665, "lon": 126.9780, "distance_km": 200, "fuel_percent": 40},
    )

    assert res.status_code == 200
    body = res.json()

    # Gemini 미설정(test) -> condition은 null, 나머지 백엔드 계산은 항상.
    assert body["condition"] is None
    assert body["hydrogen_tip"]["tip"]  # 검수 풀 본문 채움
    assert body["co2"]["saved_kg"] == 20.6  # 200km * 0.103
    assert body["nearest_station"] is not None
    assert body["nearest_station"]["chrstn_mno"]
    assert body["nearest_station"]["congestion"] is None


def test_dashboard_insights_does_not_500_without_stations(client):
    ds_module._cache.clear()
    # 충전소가 없어도 co2는 채우고 nearest_station은 null로, 500이 아니어야 한다.
    res = client.get(
        "/dashboard/insights",
        params={"lat": 33.5, "lon": 126.5, "distance_km": 0},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["co2"]["saved_kg"] == 0.0


def test_dashboard_insights_validates_latitude_range(client):
    res = client.get(
        "/dashboard/insights",
        params={"lat": 200, "lon": 126.9780, "distance_km": 10},
    )
    assert res.status_code == 422


def test_dashboard_insights_requires_distance_km(client):
    res = client.get(
        "/dashboard/insights",
        params={"lat": 37.5665, "lon": 126.9780},
    )
    assert res.status_code == 422
