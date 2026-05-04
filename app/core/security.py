import hmac
import os

from fastapi import HTTPException, Request, status


def get_configured_api_key() -> str | None:
    value = os.getenv("APP_API_KEY")
    if value is None:
        return None
    value = value.strip()
    return value or None


def is_public_path(path: str) -> bool:
    return path in {"/", "/docs", "/openapi.json", "/redoc"}


async def enforce_api_key_if_configured(request: Request) -> None:
    configured = get_configured_api_key()
    if configured is None or is_public_path(request.url.path):
        return

    provided = request.headers.get("x-api-key", "")
    if not hmac.compare_digest(provided, configured):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )
