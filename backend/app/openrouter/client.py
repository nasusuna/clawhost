"""OpenRouter Management API: create a new API key per instance (for usage/billing isolation)."""
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

OPENROUTER_KEYS_URL = "https://openrouter.ai/api/v1/keys"


def create_key(
    management_api_key: str,
    name: str,
    *,
    limit_usd: float | None = None,
    limit_reset: str | None = "monthly",
) -> str | None:
    """
    Create a new OpenRouter API key via the Management API.
    Returns the new key string (e.g. sk-or-...) or None on failure.
    The secret is only returned at creation time; caller must store it.
    """
    key = (management_api_key or "").strip()
    if not key:
        logger.warning("OpenRouter create_key: no management API key configured")
        return None
    payload: dict[str, Any] = {"name": name}
    if limit_usd is not None:
        payload["limit"] = limit_usd
    if limit_reset:
        payload["limit_reset"] = limit_reset
    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(
                OPENROUTER_KEYS_URL,
                headers={"Authorization": f"Bearer {key}"},
                json=payload,
            )
        if resp.status_code != 201:
            logger.warning(
                "OpenRouter create_key failed: status=%s body=%s",
                resp.status_code,
                resp.text[:500] if resp.text else "",
            )
            return None
        data = resp.json()
        # Response may be { "data": { "key": "sk-or-..." } } or { "key": "sk-or-..." }
        secret = None
        if isinstance(data, dict):
            inner = data.get("data", data)
            if isinstance(inner, dict):
                secret = inner.get("key") or inner.get("secret") or inner.get("token")
        if not secret or not isinstance(secret, str) or not secret.strip():
            logger.warning("OpenRouter create_key: no key in response keys=%s", list(data.keys()) if isinstance(data, dict) else "non-dict")
            return None
        return secret.strip()
    except Exception as e:
        logger.exception("OpenRouter create_key error: %s", e)
        return None


def list_keys(management_api_key: str) -> list[dict[str, Any]] | None:
    """
    List OpenRouter API keys for the account (Management API).
    Returns a list of key dicts including usage and limits, or None on failure.
    """
    key = (management_api_key or "").strip()
    if not key:
        logger.warning("OpenRouter list_keys: no management API key configured")
        return None
    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(
                OPENROUTER_KEYS_URL,
                headers={"Authorization": f"Bearer {key}"},
            )
        if resp.status_code != 200:
            logger.warning(
                "OpenRouter list_keys failed: status=%s body=%s",
                resp.status_code,
                resp.text[:500] if resp.text else "",
            )
            return None
        data = resp.json()
        # Response is typically { "data": [ {...}, ... ] }
        if isinstance(data, dict):
            items = data.get("data", data.get("keys", []))
            if isinstance(items, list):
                return [i for i in items if isinstance(i, dict)]
        if isinstance(data, list):
            return [i for i in data if isinstance(i, dict)]
        logger.warning("OpenRouter list_keys: unexpected response shape")
        return None
    except Exception as e:
        logger.exception("OpenRouter list_keys error: %s", e)
        return None
