"""Admin routes: Gemini key pool (add keys, list stats). Requires X-Admin-Secret header."""
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select

from app.config import settings
from app.db.models import GeminiKeyPool
from app.db.session import get_session
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/admin", tags=["admin"])


def _require_admin(x_admin_secret: str | None = Header(None, alias="X-Admin-Secret")) -> None:
    if not settings.admin_secret:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Admin API not configured")
    if x_admin_secret != settings.admin_secret:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid admin secret")


class AddGeminiKeyRequest(BaseModel):
    api_key: str


class AddGeminiKeyBulkRequest(BaseModel):
    api_keys: list[str]


class GeminiKeyPoolStats(BaseModel):
    available: int
    in_use: int


@router.post("/gemini-key-pool", response_model=dict)
async def add_gemini_key(
    body: AddGeminiKeyRequest,
    _: None = Depends(_require_admin),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Add one Gemini API key to the pool. Keys are assigned to new instances when no user/shared key is set."""
    key = (body.api_key or "").strip()
    if not key:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="api_key is required")
    pool_entry = GeminiKeyPool(api_key=key)
    session.add(pool_entry)
    await session.commit()
    return {"ok": True, "id": str(pool_entry.id)}


@router.post("/gemini-key-pool/bulk", response_model=dict)
async def add_gemini_keys_bulk(
    body: AddGeminiKeyBulkRequest,
    _: None = Depends(_require_admin),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Add multiple Gemini API keys to the pool."""
    keys = [k.strip() for k in (body.api_keys or []) if k and k.strip()]
    if not keys:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="api_keys must be a non-empty list")
    for key in keys:
        session.add(GeminiKeyPool(api_key=key))
    await session.commit()
    return {"ok": True, "added": len(keys)}


@router.get("/gemini-key-pool", response_model=GeminiKeyPoolStats)
async def get_gemini_key_pool_stats(
    _: None = Depends(_require_admin),
    session: AsyncSession = Depends(get_session),
) -> GeminiKeyPoolStats:
    """Return counts: available (unassigned) and in_use (assigned to an instance)."""
    available = await session.execute(
        select(func.count()).select_from(GeminiKeyPool).where(GeminiKeyPool.instance_id.is_(None))
    )
    in_use = await session.execute(
        select(func.count()).select_from(GeminiKeyPool).where(GeminiKeyPool.instance_id.isnot(None))
    )
    return GeminiKeyPoolStats(available=available.scalar() or 0, in_use=in_use.scalar() or 0)
