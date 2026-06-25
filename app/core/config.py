import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None


def load_env() -> None:
    env_path = Path(__file__).resolve().parents[2] / ".env"

    if load_dotenv is None:
        _load_dotenv_fallback(env_path)
        return

    load_dotenv(env_path, override=False)


def _load_dotenv_fallback(env_path: Path) -> None:
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].lstrip()

        key, separator, value = line.partition("=")
        if separator == "":
            continue

        key = key.strip()
        if not _is_valid_env_key(key) or key in os.environ:
            continue

        os.environ[key] = _strip_env_value(value.strip())


_TRUE_VALUES = {"1", "true", "yes", "on", "y"}


def get_env_flag(name: str, default: bool = False) -> bool:
    """환경변수를 불리언 플래그로 해석한다. (1/true/yes/on/y -> True)"""
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in _TRUE_VALUES


def is_ai_reason_enabled() -> bool:
    """충전소별 추천 사유를 Gemini AI로 생성할지 여부.
    서버 메인 설정(.env)의 AI_REASON_ENABLED로 제어하며 기본값은 False(규칙 기반)이다.
    출력 속도를 위해 기본은 꺼두고, 필요할 때만 켠다.
    """
    return get_env_flag("AI_REASON_ENABLED", default=False)


def is_dashboard_ai_enabled() -> bool:
    """대시보드 통합 인사이트를 Gemini AI로 생성할지 여부.
    충전소 추천 사유(AI_REASON_ENABLED)와 독립적인 스위치로, .env의
    DASHBOARD_AI_ENABLED로 제어한다. 기본값은 True(키가 있으면 AI 사용)이며,
    꺼두면 LLM 호출 없이 백엔드 폴백만으로 응답한다.
    """
    return get_env_flag("DASHBOARD_AI_ENABLED", default=True)


def is_nearest_ai_enabled() -> bool:
    """가까운 충전소 추천의 ai_insight.message를 Gemini AI로 생성할지 여부.
    충전소 추천 사유(AI_REASON_ENABLED), 대시보드(DASHBOARD_AI_ENABLED)와
    독립적인 스위치로, .env의 NEAREST_AI_ENABLED로 제어한다.
    기본값은 False(규칙 기반 고정 템플릿)이다.
    """
    return get_env_flag("NEAREST_AI_ENABLED", default=False)


def _is_valid_env_key(key: str) -> bool:
    if not key:
        return False
    if not (key[0].isalpha() or key[0] == "_"):
        return False
    return all(char.isalnum() or char == "_" for char in key)


def _strip_env_value(value: str) -> str:
    if len(value) < 2:
        return value
    if value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value
