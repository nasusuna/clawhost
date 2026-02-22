"""Create one Gemini API key via GCP API Keys API and store in DB. Used by script and ARQ replenish task."""
import asyncio
import logging
import os

from sqlalchemy import func, select

from app.db.models import GeminiKeyPool
from app.db.session import async_session_maker

logger = logging.getLogger(__name__)

try:
    from google.cloud import api_keys_v2
    from google.cloud.api_keys_v2.types import CreateKeyRequest
    from google.cloud.api_keys_v2.types.resources import ApiTarget, Key, Restrictions
except ImportError:
    try:
        from google.cloud.api_keys_v2.types.api_keys import CreateKeyRequest
        from google.cloud.api_keys_v2.types.resources import ApiTarget, Key, Restrictions
        from google.cloud import api_keys_v2
    except ImportError:
        api_keys_v2 = None
        CreateKeyRequest = None
        ApiTarget = Key = Restrictions = None


def create_one_key_via_gcp(project_id: str, display_name: str = "ClawHost Gemini pool") -> str:
    """Create one API key restricted to Generative Language API; return the key string. Sync (blocking)."""
    if not api_keys_v2 or CreateKeyRequest is None:
        raise RuntimeError("google-cloud-api-keys is not installed; pip install google-cloud-api-keys")
    client = api_keys_v2.ApiKeysClient()
    parent = f"projects/{project_id}/locations/global"
    key = Key(
        display_name=display_name,
        restrictions=Restrictions(
            api_targets=[ApiTarget(service="generativelanguage.googleapis.com")],
        ),
    )
    request = CreateKeyRequest(parent=parent, key=key)
    operation = client.create_key(request=request)
    result = operation.result()
    key_string = getattr(result, "key_string", None)
    if not key_string:
        key_string = client.get_key_string(name=result.name).key_string
    return key_string


async def store_key_in_pool(api_key: str) -> None:
    """Insert one key into gemini_key_pool."""
    async with async_session_maker() as session:
        session.add(GeminiKeyPool(api_key=api_key))
        await session.commit()


async def get_available_pool_count() -> int:
    """Return number of unassigned keys in pool."""
    async with async_session_maker() as session:
        r = await session.execute(
            select(func.count()).select_from(GeminiKeyPool).where(GeminiKeyPool.instance_id.is_(None))
        )
        return int(r.scalar() or 0)


async def create_and_store_one_gemini_key(project_id: str) -> bool:
    """Create one key via GCP (in thread) and store in DB. Returns True on success."""
    try:
        key_string = await asyncio.to_thread(create_one_key_via_gcp, project_id)
        await store_key_in_pool(key_string)
        logger.info("Created one Gemini API key via GCP and stored in pool.")
        return True
    except Exception as e:
        logger.warning("Failed to create/store Gemini key via GCP: %s", e, exc_info=True)
        return False
