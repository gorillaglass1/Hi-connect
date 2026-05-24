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
        "alpha": 15,
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


def test_personalized_recommendation_empty_text_to_sql_match_returns_empty_list(
    client,
    monkeypatch,
):
    async def return_empty_text_to_sql_match(self, _nl_query):
        return []

    monkeypatch.setattr(
        "app.services.recommendation_candidate_filter_service."
        "RecommendationCandidateFilterService.filter_by_natural_language",
        return_empty_text_to_sql_match,
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
            "alpha": 15,
            "nl_query": "조건에 맞는 충전소 없음",
        },
    )

    assert res.status_code == 200
    assert res.json() == []


def test_personalized_recommendation_limits_response_to_top_five(client, monkeypatch):
    async def skip_text_to_sql_filter(self, _nl_query):
        return None

    monkeypatch.setattr(
        "app.services.recommendation_candidate_filter_service."
        "RecommendationCandidateFilterService.filter_by_natural_language",
        skip_text_to_sql_filter,
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
                "chrstn_mno": f"API-REC-LIMIT-{idx}",
                "chrstn_nm": f"API 추천 제한 충전소 {idx}",
                "road_nm_addr": "인천광역시 남동구",
                "ntsl_pc": 9500 + idx,
                "let": str(37.405 + (idx * 0.001)),
                "lon": str(126.721 + (idx * 0.001)),
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
            "alpha": 50,
            "nl_query": None,
        },
    )

    assert res.status_code == 200
    assert len(res.json()) == 5
