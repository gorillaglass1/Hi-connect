def test_rest_area_weather_endpoint_returns_snake_case_payload(client, monkeypatch):
    async def fake_fetch(self, sdate, std_hour, extra_params=None):
        assert (sdate, std_hour) == ("20260617", "14")
        return {
            "code": "SUCCESS",
            "message": "정상",
            "count": 1,
            "list": [
                {
                    "stdHour": "14",
                    "unitName": "안성휴게소",
                    "routeName": "경부선",
                    "tempValue": "21.5",
                }
            ],
        }

    monkeypatch.setattr(
        "app.services.ex_highway_client.ExHighwayClient.fetch_rest_area_weather",
        fake_fetch,
    )

    res = client.get("/highway/rest-areas/weather?sdate=20260617&stdHour=14")

    assert res.status_code == 200
    body = res.json()
    assert body["code"] == "SUCCESS"
    assert body["count"] == 1
    item = body["items"][0]
    assert item["unit_name"] == "안성휴게소"
    assert item["temp_value"] == "21.5"
    # snake_case 출력 확인 (camelCase 키는 없어야 함)
    assert "unitName" not in item


def test_rest_area_weather_endpoint_requires_sdate_and_std_hour(client):
    res = client.get("/highway/rest-areas/weather?sdate=20260617")
    assert res.status_code == 422


def test_realtime_traffic_endpoint_passes_paging_and_maps_fields(client, monkeypatch):
    captured = {}

    async def fake_fetch(self, extra_params=None):
        captured["extra"] = extra_params
        return {
            "code": "SUCCESS",
            "count": 1,
            "list": [
                {
                    "vdsId": "VDS-001",
                    "trafficAmout": "1200",
                    "speed": "95",
                    "grade": "1",
                }
            ],
        }

    monkeypatch.setattr(
        "app.services.ex_highway_client.ExHighwayClient.fetch_realtime_traffic",
        fake_fetch,
    )

    res = client.get("/highway/traffic/realtime?numOfRows=5&pageNo=2")

    assert res.status_code == 200
    body = res.json()
    item = body["items"][0]
    assert item["vds_id"] == "VDS-001"
    assert item["traffic_amount"] == "1200"
    assert captured["extra"] == {"pageNo": 2, "numOfRows": 5}
