import pytest

from app.services.weather_context_service import WeatherContext, WeatherContextService


@pytest.mark.asyncio
async def test_skeleton_collect_returns_empty_context():
    # 스켈레톤 단계: 외부 호출 없이 모든 값이 None 이어야 한다.
    context = await WeatherContextService().collect(37.5665, 126.9780)
    assert isinstance(context, WeatherContext)
    assert context.to_dict() == {
        "temperature_c": None,
        "sky_state": None,
        "precipitation": None,
        "pm10": None,
        "pm25": None,
        "air_grade": None,
    }


@pytest.mark.asyncio
async def test_collect_never_raises(monkeypatch):
    service = WeatherContextService()

    def boom(*args, **kwargs):
        raise RuntimeError("KMA down")

    monkeypatch.setattr(service, "latlon_to_grid", boom)

    # 내부에서 예외가 나도 빈 컨텍스트로 폴백해야 한다(파이프라인 보호).
    context = await service.collect(37.5665, 126.9780)
    assert context.to_dict()["temperature_c"] is None


def test_latlon_to_grid_skeleton_placeholder():
    grid = WeatherContextService().latlon_to_grid(37.5665, 126.9780)
    assert (grid.nx, grid.ny) == (0, 0)
