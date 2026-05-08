from tests.services.test_optimized_station_recommendation_service import optimized_payload


def test_recommend_optimized_station_success(client):
    payload = optimized_payload()
    payload["candidate_stations"] = payload["candidate_stations"][:1]

    res = client.post("/recommendations/optimized-stations", json=payload)

    assert res.status_code == 200
    body = res.json()
    assert len(body["recommendations"]) == 3
    assert body["recommendations"][0]["hydrogen_station_id"] == body["recommended_station"]["hydrogen_station_id"]
    assert body["recommendations"][0]["highlight"]
    assert body["decision_factors"]["supports_700bar"] is True
    assert body["message_for_driver"]
