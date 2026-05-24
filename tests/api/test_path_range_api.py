def test_path_range_station_search_returns_candidate_stations(client):
    for station in [
        {
            "chrstn_mno": "API-PATH-RANGE-IN",
            "chrstn_nm": "API 경로 범위 포함 충전소",
            "let": "37.0200",
            "lon": "126.1000",
        },
        {
            "chrstn_mno": "API-PATH-RANGE-INNER",
            "chrstn_nm": "API 경로 내부 제외 충전소",
            "let": "37.1000",
            "lon": "126.1000",
        },
        {
            "chrstn_mno": "API-PATH-RANGE-OUT",
            "chrstn_nm": "API 경로 범위 외부 충전소",
            "let": "37.5000",
            "lon": "126.5000",
        },
    ]:
        client.post("/hydrogen-stations", json=station)

    response = client.post(
        "/recommendations/path-range/stations",
        json={
            "start_latitude": "37.0",
            "start_longitude": "126.0",
            "destination_latitude": "37.2",
            "destination_longitude": "126.2",
            "actual_distance_km": "40",
            "padding_km": "5",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {
        "circumscribed_box",
        "inscribed_box",
        "top_box",
        "bottom_box",
        "left_box",
        "right_box",
        "candidate_stations",
    }
    assert [station["chrstn_mno"] for station in body["candidate_stations"]] == [
        "API-PATH-RANGE-IN",
    ]


def test_path_range_station_search_rejects_route_shorter_than_straight_line(client):
    response = client.post(
        "/recommendations/path-range/stations",
        json={
            "start_latitude": "37.0",
            "start_longitude": "126.0",
            "destination_latitude": "37.2",
            "destination_longitude": "126.2",
            "actual_distance_km": "10",
        },
    )

    assert response.status_code == 400
    assert "actual route cannot be shorter" in response.json()["detail"]
