"""Contabo OAuth2 token (password grant) with in-memory cache."""
import time
from typing import Any

import httpx

from app.config import settings

CONTABO_AUTH_URL = "https://auth.contabo.com/auth/realms/contabo/protocol/openid-connect/token"

_token: str | None = None
_token_expires_at: float = 0
# Token typically valid 300s; refresh 60s before expiry
_REFRESH_BEFORE_SEC = 60


async def get_contabo_token() -> str | None:
    global _token, _token_expires_at
    if not all([
        settings.contabo_client_id,
        settings.contabo_client_secret,
        settings.contabo_api_user,
        settings.contabo_api_password,
    ]):
        return None
    now = time.time()
    if _token and _token_expires_at > now + _REFRESH_BEFORE_SEC:
        return _token
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            CONTABO_AUTH_URL,
            data={
                "grant_type": "password",
                "client_id": settings.contabo_client_id,
                "client_secret": settings.contabo_client_secret,
                "username": settings.contabo_api_user,
                "password": settings.contabo_api_password,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    if resp.status_code != 200:
        _token = None
        return None
    body: dict[str, Any] = resp.json()
    _token = body.get("access_token")
    expires_in = body.get("expires_in", 300)
    _token_expires_at = now + expires_in
    return _token


def _clear_token() -> None:
    global _token, _token_expires_at
    _token = None
    _token_expires_at = 0
