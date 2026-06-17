def test_personalized_recommendation_returns_queue_time_estimate_in_payload(
    client,
    monkeypatch,
):
    async def use_queue_estimate_api_station(self, _nl_query):
        return ["API-QUEUE-ESTIMATE"]

    monkeypatch.setattr(
        "app.services.recommendation_candidate_filter_service."
        "RecommendationCandidateFilterService.filter_by_natural_language",
        use_queue_estimate_api_station,
    )

    user_res = client.post(
        "/users",
        json={
            "name": "API 대기시간 예측 사용자",
            "phone": "010-3333-9991",
            "email": "api-queue-estimate-user@example.com",
        },
    )
    user_id = user_res.json()["user_id"]
    client.post(
        "/hydrogen-stations",
        json={
            "chrstn_mno": "API-QUEUE-ESTIMATE",
            "chrstn_nm": "API 대기시간 예측 충전소",
            "ntsl_pc": 10000,
            "cmpt_yn": "Y",
            "let": "37.0000",
            "lon": "127.1000",
            "oper_yn": "Y",
        },
    )
    client.post(
        "/hydrogen-station-status",
        json={
            "chrstn_mno": "API-QUEUE-ESTIMATE",
            "wait_vhcle_alge": 4,
            "tt_pressr": 700,
            "prfect_elctc_posbl_alge": 10,
            "oper_sttus_nm": "운영중",
            "pos_sttus_nm": "영업중",
        },
    )

    res = client.post(
        "/recommendations/personalized",
        json={
            "user_id": user_id,
            "current_latitude": 37.0,
            "current_longitude": 127.0,
            "destination_latitude": 37.0,
            "destination_longitude": 127.2,
            "remaining_range": 100,
            "nl_query": "API 대기시간 예측 충전소만",
        },
    )

    assert res.status_code == 200
    top = res.json()[0]
    assert top["wait_vehicles"] == 4
    assert top["wait_time_minutes"] == 15
    assert top["wait_time_minutes"] != top["wait_vehicles"] * 15
    assert top["delivery_payload"]["wait_time_minutes"] == top["wait_time_minutes"]
    assert top["delivery_payload"]["wait_vehicles"] == top["wait_vehicles"]


def test_personalized_recommendation_returns_delivery_payload(client, monkeypatch):
    async def use_only_api_test_stations(self, _nl_query):
        return ["API-REC-ST-001", "API-REC-ST-002"]

    monkeypatch.setattr(
        "app.services.recommendation_candidate_filter_service."
        "RecommendationCandidateFilterService.filter_by_natural_language",
        use_only_api_test_stations,
    )

    user_res = client.post(
        "/users",
        json={
            "name": "API 추천 사용자",
            "phone": "010-3333-4444",
            "email": "api-rec-user@example.com",
        },
    )
    user_id = user_res.json()["user_id"]

    client.put(
        f"/users/{user_id}/preferences",
        json={
            "weight_price": "2.5",
            "weight_waiting_time": "1.5",
            "weight_distance": "0.5",
            "weight_facilities": "0.0",
            "safety_margin": "1.1",
        },
    )
    client.post(
        "/hydrogen-stations",
        json={
            "chrstn_mno": "API-REC-ST-001",
            "chrstn_nm": "API 추천 가까운 충전소",
            "road_nm_addr": "인천광역시 남동구",
            "ntsl_pc": 9500,
            "let": "37.4100",
            "lon": "126.7000",
            "oper_yn": "Y",
        },
    )
    client.post(
        "/hydrogen-stations",
        json={
            "chrstn_mno": "API-REC-ST-002",
            "chrstn_nm": "API 추천 먼 충전소",
            "road_nm_addr": "인천광역시 중구",
            "ntsl_pc": 11000,
            "let": "37.4500",
            "lon": "126.5000",
            "oper_yn": "Y",
        },
    )
    client.post(
        "/hydrogen-station-status",
        json={
            "chrstn_mno": "API-REC-ST-001",
            "wait_vhcle_alge": 0,
            "oper_sttus_nm": "운영중",
            "pos_sttus_nm": "영업중",
        },
    )
    client.post(
        "/hydrogen-station-facilities",
        json={
            "chrstn_mno": "API-REC-ST-001",
            "adi_info_se_nm": "편의점",
        },
    )

    request_payload = {
        "user_id": user_id,
        "current_latitude": 37.405,
        "current_longitude": 126.721,
        "destination_latitude": 37.46,
        "destination_longitude": 126.45,
        "remaining_range": 45,
        "nl_query": "인천에 있고 대기 차량이 적은 충전소",
    }

    res = client.post(
        "/recommendations/personalized",
        json=request_payload,
    )

    assert res.status_code == 200
    body = res.json()
    assert len(body) > 0
    top = body[0]
    assert top["chrstn_mno"] == "API-REC-ST-001"
    assert top["delivery_payload"]["chrstn_mno"] == "API-REC-ST-001"
    assert top["delivery_payload"]["chrstn_nm"] == top["chrstn_nm"]
    assert top["delivery_payload"]["latitude"] == 37.41
    assert top["delivery_payload"]["longitude"] == 126.7
    assert top["delivery_payload"]["distance_to_station"] == top["distance_to_station"]
    assert top["delivery_payload"]["detour_distance"] == top["detour_distance"]
    assert top["delivery_payload"]["wait_vehicles"] == top["wait_vehicles"]
    assert top["delivery_payload"]["facilities"] == top["facilities"]
    assert top["delivery_payload"]["final_score"] == top["final_score"]
    assert "hyundai_nav_deeplink" not in top
    assert "hyundai_nav_deeplink" not in top["delivery_payload"]

    vehicle_res = client.post(
        "/recommendations/personalized/delivery-payloads",
        json=request_payload,
    )
    assert vehicle_res.status_code == 200
    vehicle_payload = vehicle_res.json()[0]
    assert vehicle_payload["chrstn_mno"] == "API-REC-ST-001"
    assert "delivery_payload" not in vehicle_payload
    assert "sub_scores" not in vehicle_payload
    assert "hyundai_nav_deeplink" not in vehicle_payload


def test_personalized_recommendation_empty_rule_based_match_returns_empty_list(
    client,
    monkeypatch,
):
    async def return_empty_rule_based_match(self, _nl_query):
        return []

    monkeypatch.setattr(
        "app.services.recommendation_candidate_filter_service."
        "RecommendationCandidateFilterService.filter_by_natural_language",
        return_empty_rule_based_match,
    )

    user_res = client.post(
        "/users",
        json={
            "name": "API 추천 빈 결과 사용자",
            "phone": "010-3333-5555",
            "email": "api-rec-empty-user@example.com",
        },
    )
    user_id = user_res.json()["user_id"]

    res = client.post(
        "/recommendations/personalized",
        json={
            "user_id": user_id,
            "current_latitude": 37.405,
            "current_longitude": 126.721,
            "destination_latitude": 37.46,
            "destination_longitude": 126.45,
            "remaining_range": 45,
            "nl_query": "조건에 맞는 충전소 없음",
        },
    )

    assert res.status_code == 200
    assert res.json() == []


def test_personalized_recommendation_exposes_detour_distance_scenarios(
    client,
    monkeypatch,
):
    async def use_detour_api_stations(self, _nl_query):
        return ["API-DETOUR-LOW", "API-DETOUR-HIGH"]

    monkeypatch.setattr(
        "app.services.recommendation_candidate_filter_service."
        "RecommendationCandidateFilterService.filter_by_natural_language",
        use_detour_api_stations,
    )

    user_res = client.post(
        "/users",
        json={
            "name": "API 우회거리 사용자",
            "phone": "010-3333-7777",
            "email": "api-detour-user@example.com",
        },
    )
    user_id = user_res.json()["user_id"]

    client.put(
        f"/users/{user_id}/preferences",
        json={
            "weight_price": "0.0",
            "weight_waiting_time": "0.0",
            "weight_distance": "3.0",
            "weight_facilities": "0.0",
            "safety_margin": "1.0",
        },
    )
    client.post(
        "/hydrogen-stations",
        json={
            "chrstn_mno": "API-DETOUR-LOW",
            "chrstn_nm": "API 목적지 방향 저우회 충전소",
            "road_nm_addr": "경로상",
            "ntsl_pc": 10000,
            "let": "37.0000",
            "lon": "127.1000",
            "oper_yn": "Y",
        },
    )
    client.post(
        "/hydrogen-stations",
        json={
            "chrstn_mno": "API-DETOUR-HIGH",
            "chrstn_nm": "API 가까워 보이는 고우회 충전소",
            "road_nm_addr": "경로 외곽",
            "ntsl_pc": 10000,
            "let": "37.0900",
            "lon": "127.0000",
            "oper_yn": "Y",
        },
    )

    request_payload = {
        "user_id": user_id,
        "current_latitude": 37.0,
        "current_longitude": 127.0,
        "destination_latitude": 37.0,
        "destination_longitude": 127.2,
        "remaining_range": 100,
        "nl_query": "우회거리 테스트 충전소만",
    }
    res = client.post("/recommendations/personalized", json=request_payload)

    assert res.status_code == 200
    body = res.json()
    assert [item["chrstn_mno"] for item in body] == [
        "API-DETOUR-LOW",
        "API-DETOUR-HIGH",
    ]
    assert body[0]["detour_distance"] < 0.1
    assert body[1]["detour_distance"] > 10.0
    assert body[0]["sub_scores"]["distance"] > body[1]["sub_scores"]["distance"]
    assert body[0]["delivery_payload"]["detour_distance"] == body[0]["detour_distance"]

    vehicle_res = client.post(
        "/recommendations/personalized/delivery-payloads",
        json=request_payload,
    )
    assert vehicle_res.status_code == 200
    vehicle_payloads = vehicle_res.json()
    assert vehicle_payloads[0]["detour_distance"] < vehicle_payloads[1]["detour_distance"]


def test_personalized_recommendation_can_use_path_range_filter(client, monkeypatch):
    async def use_only_api_path_range_test_stations(self, _nl_query):
        return [
            "API-REC-PATH-RANGE-IN",
            "API-REC-PATH-RANGE-INNER",
            "API-REC-PATH-RANGE-OUT",
        ]

    monkeypatch.setattr(
        "app.services.recommendation_candidate_filter_service."
        "RecommendationCandidateFilterService.filter_by_natural_language",
        use_only_api_path_range_test_stations,
    )

    user_res = client.post(
        "/users",
        json={
            "name": "API 실경로 추천 사용자",
            "phone": "010-3333-8888",
            "email": "api-path-range-rec-user@example.com",
        },
    )
    user_id = user_res.json()["user_id"]

    for station in [
        {
            "chrstn_mno": "API-REC-PATH-RANGE-IN",
            "chrstn_nm": "API 추천 경로 범위 포함 충전소",
            "let": "36.4200",
            "lon": "128.5000",
            "oper_yn": "Y",
        },
        {
            "chrstn_mno": "API-REC-PATH-RANGE-INNER",
            "chrstn_nm": "API 추천 경로 내부 제외 충전소",
            "let": "36.5000",
            "lon": "128.5000",
            "oper_yn": "Y",
        },
        {
            "chrstn_mno": "API-REC-PATH-RANGE-OUT",
            "chrstn_nm": "API 추천 경로 범위 외부 충전소",
            "let": "36.9000",
            "lon": "128.9000",
            "oper_yn": "Y",
        },
    ]:
        client.post("/hydrogen-stations", json=station)

    response = client.post(
        "/recommendations/personalized/delivery-payloads",
        json={
            "user_id": user_id,
            "current_latitude": 36.4,
            "current_longitude": 128.4,
            "destination_latitude": 36.6,
            "destination_longitude": 128.6,
            "remaining_range": 100,
            "nl_query": None,
        },
    )

    assert response.status_code == 200
    assert {item["chrstn_mno"] for item in response.json()} == {
        "API-REC-PATH-RANGE-IN",
        "API-REC-PATH-RANGE-INNER",
    }


def test_personalized_recommendation_limits_response_to_top_five(client, monkeypatch):
    limit_station_ids = [f"API-REC-LIMIT-{idx}" for idx in range(6)]

    async def use_only_limit_test_stations(self, _nl_query):
        return limit_station_ids

    monkeypatch.setattr(
        "app.services.recommendation_candidate_filter_service."
        "RecommendationCandidateFilterService.filter_by_natural_language",
        use_only_limit_test_stations,
    )

    user_res = client.post(
        "/users",
        json={
            "name": "API 추천 제한 사용자",
            "phone": "010-3333-6666",
            "email": "api-rec-limit-user@example.com",
        },
    )
    user_id = user_res.json()["user_id"]

    for idx in range(6):
        client.post(
            "/hydrogen-stations",
            json={
                "chrstn_mno": limit_station_ids[idx],
                "chrstn_nm": f"API 추천 제한 충전소 {idx}",
                "road_nm_addr": "인천광역시 남동구",
                "ntsl_pc": 9500 + idx,
                "let": str(37.405 + (idx * 0.001)),
                "lon": str(126.721 - (idx * 0.01)),
                "oper_yn": "Y",
            },
        )

    res = client.post(
        "/recommendations/personalized",
        json={
            "user_id": user_id,
            "current_latitude": 37.405,
            "current_longitude": 126.721,
            "destination_latitude": 37.46,
            "destination_longitude": 126.45,
            "remaining_range": 100,
            "nl_query": "응답 제한 테스트 충전소만",
        },
    )

    assert res.status_code == 200
    assert len(res.json()) == 5
