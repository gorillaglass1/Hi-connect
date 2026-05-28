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
