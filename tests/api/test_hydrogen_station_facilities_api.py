def test_create_and_list_hydrogen_station_facility(client):
    client.post(
        "/hydrogen-stations",
        json={
            "chrstn_mno": "API-FAC-001",
            "chrstn_nm": "API 부대시설 테스트 충전소",
        },
    )

    create_res = client.post(
        "/hydrogen-station-facilities",
        json={
            "chrstn_mno": "API-FAC-001",
            "adi_info_se_cd": "PARK",
            "adi_info_se_nm": "주차장",
        },
    )
    assert create_res.status_code == 201
    assert create_res.json()["adi_info_se_cd"] == "PARK"

    list_res = client.get(
        "/hydrogen-station-facilities",
        params={"chrstn_mno": "API-FAC-001"},
    )
    assert list_res.status_code == 200
    assert list_res.json()[0]["adi_info_se_nm"] == "주차장"
