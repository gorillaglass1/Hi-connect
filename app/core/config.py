from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None


def load_env() -> None:
    if load_dotenv is None:
        return

    env_path = Path(__file__).resolve().parents[2] / ".env"
    load_dotenv(env_path, override=False)
