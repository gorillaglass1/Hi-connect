import pytest

from app.services.ex_highway_service import ExHighwayService


class FakeExHighwayClient:
    def __init__(self, weather_payload=None, traffic_payload=None):
        self.weather_payload = weather_payload
        self.traffic_payload = traffic_payload
        self.weather_args = None
        self.traffic_args = None

    async def fetch_rest_area_weather(self, sdate, std_hour, extra_params=None):
        self.weather_args = (sdate, std_hour, extra_params)
        return self.weather_payload

    async def fetch_realtime_traffic(self, extra_params=None):
        self.traffic_args = extra_params
        return self.traffic_payload


@pytest.mark.asyncio
async def test_get_rest_area_weather_maps_fields_and_metadata():
    payload = {
        "code": "SUCCESS",
        "message": "정상",
        "count": 1,
        "list": [
            {
                "sdate": "20260617",
                "stdHour": "14",
                "unitCode": "001",
                "unitName": "안성휴게소",
                "routeNo": "0010",
                "routeName": "경부선",
                "updownTypeCode": "S",
                "tempValue": "21.5",
                "humidityValue": "60",
                "weatherContents": "맑음",
                "windValue": "1.2",
            }
        ],
    }
    service = ExHighwayService(client=FakeExHighwayClient(weather_payload=payload))

    result = await service.get_rest_area_weather("20260617", "14")

    assert result.code == "SUCCESS"
    assert result.message == "정상"
    assert result.count == 1
    assert len(result.items) == 1
    item = result.items[0]
    assert item.unit_name == "안성휴게소"
    assert item.route_name == "경부선"
    assert item.temp_value == "21.5"
    assert item.humidity_value == "60"
    assert item.weather_contents == "맑음"
    assert service.client.weather_args == ("20260617", "14", None)


@pytest.mark.asyncio
async def test_get_realtime_traffic_maps_typo_field_and_count_fallback():
    payload = {
        "code": "SUCCESS",
        "message": "정상",
        # count 누락 -> 항목 수로 폴백
        "list": [
            {
                "stdDate": "20260617",
                "stdHour": "14",
                "vdsId": "VDS-001",
                "trafficAmout": "1200",
                "speed": "95",
                "grade": "1",
                "routeName": "경부선",
                "conzoneName": "서울TG-기흥",
            }
        ],
    }
    service = ExHighwayService(client=FakeExHighwayClient(traffic_payload=payload))

    result = await service.get_realtime_traffic({"numOfRows": 10})

    assert result.code == "SUCCESS"
    assert result.count == 1  # count 누락 시 항목 수로 폴백
    assert len(result.items) == 1
    item = result.items[0]
    assert item.traffic_amount == "1200"  # API 오타 키(trafficAmout) 매핑
    assert item.speed == "95"
    assert item.grade == "1"
    assert item.conzone_name == "서울TG-기흥"
    assert service.client.traffic_args == {"numOfRows": 10}


@pytest.mark.asyncio
async def test_extract_items_handles_unknown_list_key():
    payload = {"code": "SUCCESS", "weatherList": [{"unitName": "죽암휴게소"}]}
    service = ExHighwayService(client=FakeExHighwayClient(weather_payload=payload))

    result = await service.get_rest_area_weather("20260617", "09")

    assert [item.unit_name for item in result.items] == ["죽암휴게소"]


@pytest.mark.asyncio
async def test_empty_payload_yields_empty_items():
    service = ExHighwayService(client=FakeExHighwayClient(weather_payload={}))

    result = await service.get_rest_area_weather("20260617", "09")

    assert result.items == []
    assert result.count == 0
