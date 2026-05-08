from pathlib import Path


GEMINI_PROPERTIES_PATH = Path(__file__).with_name("gemini.properties")


def read_properties(path: Path = GEMINI_PROPERTIES_PATH) -> dict[str, str]:
    if not path.exists():
        return {}

    properties: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        properties[key.strip()] = value.strip()
    return properties


def get_gemini_api_key() -> str | None:
    value = read_properties().get("GEMINI_API_KEY")
    if value is None:
        return None
    value = value.strip()
    if not value or value == "replace-with-your-gemini-api-key":
        return None
    return value


def get_gemini_model() -> str:
    return read_properties().get("GEMINI_MODEL", "gemini-1.5-flash").strip() or "gemini-1.5-flash"
