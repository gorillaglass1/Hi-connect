import pytest

from app.core.config import get_env_flag, is_ai_reason_enabled


@pytest.mark.parametrize(
    "value,expected",
    [
        ("true", True),
        ("True", True),
        ("1", True),
        ("on", True),
        ("yes", True),
        ("y", True),
        ("false", False),
        ("0", False),
        ("off", False),
        ("", False),
        ("   ", False),
    ],
)
def test_get_env_flag_parses_truthy_values(monkeypatch, value, expected):
    monkeypatch.setenv("SOME_TEST_FLAG", value)
    assert get_env_flag("SOME_TEST_FLAG", default=False) is expected


def test_get_env_flag_uses_default_when_unset(monkeypatch):
    monkeypatch.delenv("SOME_TEST_FLAG", raising=False)
    assert get_env_flag("SOME_TEST_FLAG", default=False) is False
    assert get_env_flag("SOME_TEST_FLAG", default=True) is True


def test_ai_reason_disabled_by_default(monkeypatch):
    monkeypatch.delenv("AI_REASON_ENABLED", raising=False)
    assert is_ai_reason_enabled() is False


def test_ai_reason_enabled_when_switched_on(monkeypatch):
    monkeypatch.setenv("AI_REASON_ENABLED", "true")
    assert is_ai_reason_enabled() is True
