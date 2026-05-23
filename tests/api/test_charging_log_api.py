def test_create_charging_logs_with_multiple_stations(client):
    for station in [
        {
            "chrstn_mno": "LOG-ST-001",
            "chrstn_nm": "로그 테스트 충전소 1",
        },
        {
            "chrstn_mno": "LOG-ST-002",
            "chrstn_nm": "로그 테스트 충전소 2",
        },
    ]:
        client.post("/hydrogen-stations", json=station)

    res = client.post(
        "/charging-logs",
        json={
            "user_id": 1,
            "logs": [
                {
                    "chrstn_mno": "LOG-ST-001",
                    "start_time": "2026-05-22T08:10:00",
                    "end_time": "2026-05-22T08:24:00",
                    "charged_amount": "3.80",
                    "charging_cost": "36860.00",
                    "waiting_time": 0,
                },
                {
                    "chrstn_mno": "LOG-ST-002",
                    "start_time": "2026-05-22T09:00:00",
                    "end_time": "2026-05-22T09:18:00",
                    "charged_amount": "4.10",
                    "charging_cost": "40590.00",
                    "waiting_time": 3,
                },
            ],
        },
    )

    assert res.status_code == 201
    body = res.json()
    assert len(body) == 2
    assert [row["chrstn_mno"] for row in body] == ["LOG-ST-001", "LOG-ST-002"]
    assert body[0]["user_id"] == 1


def test_create_charging_logs_invalid_time_returns_400(client):
    client.post(
        "/hydrogen-stations",
        json={
            "chrstn_mno": "LOG-ST-BAD-TIME",
            "chrstn_nm": "로그 시간 검증 충전소",
        },
    )

    res = client.post(
        "/charging-logs",
        json={
            "user_id": 1,
            "logs": [
                {
                    "chrstn_mno": "LOG-ST-BAD-TIME",
                    "start_time": "2026-05-22T09:00:00",
                    "end_time": "2026-05-22T08:59:00",
                }
            ],
        },
    )

    assert res.status_code == 400


def test_list_charging_logs_filters_by_user_and_station(client):
    client.post(
        "/hydrogen-stations",
        json={
            "chrstn_mno": "LOG-ST-LIST-001",
            "chrstn_nm": "로그 목록 충전소",
        },
    )
    client.post(
        "/charging-logs",
        json={
            "user_id": 2,
            "logs": [
                {
                    "chrstn_mno": "LOG-ST-LIST-001",
                    "start_time": "2026-05-22T10:00:00",
                    "end_time": "2026-05-22T10:20:00",
                }
            ],
        },
    )

    res = client.get(
        "/charging-logs",
        params={
            "user_id": 2,
            "chrstn_mno": "LOG-ST-LIST-001",
        },
    )

    assert res.status_code == 200
    body = res.json()
    assert len(body) == 1
    assert body[0]["chrstn_mno"] == "LOG-ST-LIST-001"
