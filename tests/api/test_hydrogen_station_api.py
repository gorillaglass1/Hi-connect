def test_create_and_list_hydrogen_station(client):
    create_res = client.post(
        "/hydrogen-stations",
        json={
            "chrstn_mno": "API-ST-001",
            "chrstn_nm": "API 테스트 충전소",
            "road_nm_addr": "서울시 강남구",
        },
    )
    assert create_res.status_code == 201
    assert create_res.json()["chrstn_mno"] == "API-ST-001"

    list_res = client.get("/hydrogen-stations", params={"chrstn_mno": "API-ST-001"})
    assert list_res.status_code == 200
    assert list_res.json()[0]["chrstn_nm"] == "API 테스트 충전소"


def test_get_hydrogen_station_detail(client):
    client.post(
        "/hydrogen-stations",
        json={
            "chrstn_mno": "API-ST-DETAIL-001",
            "chrstn_nm": "API 상세 충전소",
        },
    )
    client.post(
        "/hydrogen-station-status",
        json={
            "chrstn_mno": "API-ST-DETAIL-001",
            "oper_sttus_nm": "운영중",
        },
    )
    client.post(
        "/hydrogen-station-facilities",
        json={
            "chrstn_mno": "API-ST-DETAIL-001",
            "adi_info_se_nm": "화장실",
        },
    )

    res = client.get("/hydrogen-stations/API-ST-DETAIL-001")

    assert res.status_code == 200
    body = res.json()
    assert body["chrstn_nm"] == "API 상세 충전소"
    assert body["status"]["oper_sttus_nm"] == "운영중"
    assert body["facilities"][0]["adi_info_se_nm"] == "화장실"


def test_get_hydrogen_station_detail_missing_returns_404(client):
    res = client.get("/hydrogen-stations/UNKNOWN")

    assert res.status_code == 404


def test_list_hydrogen_station_details_by_conditions(client):
    client.post(
        "/hydrogen-stations",
        json={
            "chrstn_mno": "API-ST-SEARCH-001",
            "chrstn_nm": "API 서울 조건 충전소",
            "road_nm_addr": "서울시 마포구",
            "oper_yn": "Y",
            "rltm_info_yn": "Y",
            "rsvt_posbl_yn": "N",
        },
    )
    client.post(
        "/hydrogen-stations",
        json={
            "chrstn_mno": "API-ST-SEARCH-002",
            "chrstn_nm": "API 경기 조건 충전소",
            "road_nm_addr": "경기도 성남시",
            "oper_yn": "Y",
            "rltm_info_yn": "N",
            "rsvt_posbl_yn": "Y",
        },
    )
    client.post(
        "/hydrogen-station-status",
        json={
            "chrstn_mno": "API-ST-SEARCH-001",
            "oper_sttus_nm": "운영중",
            "pos_sttus_nm": "영업중",
            "cnf_sttus_nm": "여유",
        },
    )
    client.post(
        "/hydrogen-station-status",
        json={
            "chrstn_mno": "API-ST-SEARCH-002",
            "oper_sttus_nm": "운영중",
            "pos_sttus_nm": "영업마감",
            "cnf_sttus_nm": "혼잡",
        },
    )
    client.post(
        "/hydrogen-station-facilities",
        json={
            "chrstn_mno": "API-ST-SEARCH-001",
            "adi_info_se_nm": "편의점",
        },
    )

    res = client.get(
        "/hydrogen-stations/details",
        params={
            "address": "서울",
            "oper_yn": "Y",
            "rltm_info_yn": "Y",
            "pos_sttus_nm": "영업중",
            "facility_nm": "편의점",
        },
    )

    assert res.status_code == 200
    body = res.json()
    assert len(body) == 1
    assert body[0]["chrstn_mno"] == "API-ST-SEARCH-001"
    assert body[0]["status"]["pos_sttus_nm"] == "영업중"
    assert body[0]["facilities"][0]["adi_info_se_nm"] == "편의점"


def test_list_hydrogen_station_details_filters_address_prefix_and_sorts_wait_queue(
    client,
):
    for station in [
        {
            "chrstn_mno": "API-ST-INCHEON-001",
            "chrstn_nm": "API 인천 대기 많음",
            "road_nm_addr": "인천API광역시 남동구",
        },
        {
            "chrstn_mno": "API-ST-INCHEON-002",
            "chrstn_nm": "API 인천 대기 적음",
            "road_nm_addr": "인천API광역시 연수구",
        },
        {
            "chrstn_mno": "API-ST-NOT-INCHEON-001",
            "chrstn_nm": "API 주소 중간 인천",
            "road_nm_addr": "서울특별시 인천API로",
        },
    ]:
        client.post("/hydrogen-stations", json=station)

    for status in [
        {
            "chrstn_mno": "API-ST-INCHEON-001",
            "pos_sttus_nm": "영업중",
            "wait_vhcle_alge": 4,
        },
        {
            "chrstn_mno": "API-ST-INCHEON-002",
            "pos_sttus_nm": "영업중",
            "wait_vhcle_alge": 1,
        },
        {
            "chrstn_mno": "API-ST-NOT-INCHEON-001",
            "pos_sttus_nm": "영업중",
            "wait_vhcle_alge": 0,
        },
    ]:
        client.post("/hydrogen-station-status", json=status)

    res = client.get(
        "/hydrogen-stations/details",
        params={
            "address": "인천API",
            "pos_sttus_nm": "영업중",
            "sort_by": "wait_vhcle_alge",
            "sort_order": "asc",
        },
    )

    assert res.status_code == 200
    body = res.json()
    assert [row["chrstn_mno"] for row in body] == [
        "API-ST-INCHEON-002",
        "API-ST-INCHEON-001",
    ]
    assert [row["status"]["wait_vhcle_alge"] for row in body] == [1, 4]
