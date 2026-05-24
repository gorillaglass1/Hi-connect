def test_create_and_list_hydrogen_station_status(client):
    client.post(
        "/hydrogen-stations",
        json={
            "chrstn_mno": "API-STATUS-001",
            "chrstn_nm": "API 상태 테스트 충전소",
        },
    )

    create_res = client.post(
        "/hydrogen-station-status",
        json={
            "chrstn_mno": "API-STATUS-001",
            "tt_pressr": 700,
            "oper_sttus_cd": "OPEN",
            "oper_sttus_nm": "운영중",
        },
    )
    assert create_res.status_code == 201
    assert create_res.json()["oper_sttus_nm"] == "운영중"

    list_res = client.get(
        "/hydrogen-station-status",
        params={"chrstn_mno": "API-STATUS-001"},
    )
    assert list_res.status_code == 200
    assert list_res.json()[0]["tt_pressr"] == 700
