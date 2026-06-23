import time

import pytest

from app.services import dashboard_llm_service as llm_module
from app.services.dashboard_llm_service import DashboardLlmService, LlmInsight

_GOOD_JSON = (
    '{"station_sql":"SELECT chrstn_mno, chrstn_nm, lon, let FROM hydrogen_stations",'
    '"condition":{"score":80,"grade":"좋음","briefing":"안전 운전하세요"},'
    '"hydrogen_tip":{"tip_id":"tip_cold_01","context_label":"기온 -2°C 감지","reason":"오늘 날씨에 맞춰 추천"}}'
)


# --- _parse ---------------------------------------------------------------
def test_parse_valid_json():
    insight = DashboardLlmService._parse(_GOOD_JSON)
    assert insight.station_sql.startswith("SELECT")
    assert insight.condition["score"] == 80
    assert insight.hydrogen_tip["tip_id"] == "tip_cold_01"


def test_parse_strips_code_fence_and_junk():
    raw = "여기 결과:\n```json\n" + _GOOD_JSON + "\n```"
    insight = DashboardLlmService._parse(raw)
    assert insight is not None
    assert insight.condition["grade"] == "좋음"


def test_parse_returns_none_for_invalid_json():
    assert DashboardLlmService._parse("그냥 텍스트") is None


def test_parse_returns_none_for_non_object():
    assert DashboardLlmService._parse("[1, 2, 3]") is None


def test_parse_defaults_missing_fields():
    insight = DashboardLlmService._parse('{"station_sql": 123}')
    assert insight.station_sql == ""  # 문자열이 아니면 빈 문자열
    assert insight.condition == {}
    assert insight.hydrogen_tip == {}


# --- prompt builder -------------------------------------------------------
def test_prompt_includes_schema_and_tip_catalog():
    prompt = DashboardLlmService._build_prompt(
        {"위치": {"lat": 37.5, "lon": 127.0}},
        [{"tip_id": "tip_cold_01", "tags": ["cold"], "title": "한파"}],
    )
    assert "hydrogen_stations" in prompt
    assert "let" in prompt  # 좌표 위도 컬럼 안내
    assert "tip_cold_01" in prompt
    assert "haversine" in prompt  # 거리 계산은 백엔드라는 지시


# --- generate -------------------------------------------------------------
@pytest.mark.asyncio
async def test_generate_returns_none_without_client():
    service = DashboardLlmService()
    service.client = None
    assert await service.generate({}, []) is None


@pytest.mark.asyncio
async def test_generate_parses_model_output(monkeypatch):
    service = DashboardLlmService()
    service.client = object()
    monkeypatch.setattr(service, "_call_model", lambda prompt: _GOOD_JSON)

    insight = await service.generate({"위치": {}}, [])

    assert isinstance(insight, LlmInsight)
    assert insight.hydrogen_tip["tip_id"] == "tip_cold_01"


@pytest.mark.asyncio
async def test_generate_returns_none_on_model_error(monkeypatch):
    service = DashboardLlmService()
    service.client = object()

    def boom(prompt):
        raise RuntimeError("Gemini error")

    monkeypatch.setattr(service, "_call_model", boom)
    assert await service.generate({}, []) is None


@pytest.mark.asyncio
async def test_generate_times_out(monkeypatch):
    service = DashboardLlmService()
    service.client = object()
    # 타임아웃을 아주 짧게 줄이고, 모델 호출은 그보다 오래 걸리게 한다.
    monkeypatch.setattr(llm_module, "LLM_TIMEOUT_SECONDS", 0.05)

    def slow(prompt):
        time.sleep(0.3)
        return _GOOD_JSON

    monkeypatch.setattr(service, "_call_model", slow)
    assert await service.generate({}, []) is None
