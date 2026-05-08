from tests.services.test_optimized_station_recommendation_service import optimized_payload


def test_recommend_optimized_station_success(client):
    res = client.post("/recommendations/optimized-stations", json=optimized_payload())

    assert res.status_code == 200
    body = res.json()
    assert body["recommended_station"]["hydrogen_station_id"] == 101
    assert body["decision_factors"]["supports_700bar"] is True
    assert body["message_for_driver"]
