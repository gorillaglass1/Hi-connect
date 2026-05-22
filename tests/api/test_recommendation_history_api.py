def test_create_recommendation_histories_with_multiple_stations(client):
    for station in [
        {
            "chrstn_mno": "REC-ST-001",
            "chrstn_nm": "추천 테스트 충전소 1",
            "road_nm_addr": "인천광역시 연수구",
        },
        {
            "chrstn_mno": "REC-ST-002",
            "chrstn_nm": "추천 테스트 충전소 2",
            "road_nm_addr": "인천광역시 남동구",
        },
    ]:
        client.post("/hydrogen-stations", json=station)

    res = client.post(
        "/recommendation-histories",
        json={
            "user_id": 1,
            "vehicle_id": 10,
            "user_latitude": "37.3900000",
            "user_longitude": "126.6500000",
            "vehicle_remaining_hydrogen": "32.50",
            "recommendations": [
                {
                    "chrstn_mno": "REC-ST-001",
                    "recommendation_score": "96.50",
                    "recommendation_reason": "대기 차량이 적습니다.",
                    "estimated_arrival_time": 8,
                    "selected": True,
                    "recommendation_type": "LOW_WAIT",
                },
                {
                    "chrstn_mno": "REC-ST-002",
                    "recommendation_score": "88.00",
                    "recommendation_reason": "가까운 충전소입니다.",
                    "estimated_arrival_time": 12,
                    "selected": False,
                    "recommendation_type": "NEARBY",
                },
            ],
        },
    )

    assert res.status_code == 201
    body = res.json()
    assert len(body) == 2
    assert [row["chrstn_mno"] for row in body] == ["REC-ST-001", "REC-ST-002"]
    assert body[0]["user_id"] == 1
    assert body[0]["vehicle_id"] == 10


def test_list_recommendation_histories_filters_by_user_and_station(client):
    client.post(
        "/hydrogen-stations",
        json={
            "chrstn_mno": "REC-ST-LIST-001",
            "chrstn_nm": "추천 목록 충전소",
        },
    )
    client.post(
        "/recommendation-histories",
        json={
            "user_id": 2,
            "vehicle_id": 20,
            "recommendations": [
                {
                    "chrstn_mno": "REC-ST-LIST-001",
                    "recommendation_score": "91.00",
                    "recommendation_type": "LOW_WAIT",
                }
            ],
        },
    )

    res = client.get(
        "/recommendation-histories",
        params={
            "user_id": 2,
            "chrstn_mno": "REC-ST-LIST-001",
        },
    )

    assert res.status_code == 200
    body = res.json()
    assert len(body) == 1
    assert body[0]["chrstn_mno"] == "REC-ST-LIST-001"
    assert body[0]["recommendation_type"] == "LOW_WAIT"
