"""Usage routes: current user's LLM usage per instance (for dashboard).

Prefer OpenRouter per-key usage when Management API key is configured; fall back to Gemini DB usage otherwise.
"""
import calendar
from datetime import date

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select

from app.auth.deps import get_current_user
from app.config import settings
from app.db.models import Instance, GeminiUsage, User
from app.db.session import get_session
from app.openrouter.client import list_keys as openrouter_list_keys
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/usage", tags=["usage"])


def _period_end_for(d: date) -> date:
    """Last day of the month."""
    _, last = calendar.monthrange(d.year, d.month)
    return date(d.year, d.month, last)


class InstanceUsageResponse(BaseModel):
    instance_id: str
    domain: str | None
    used_usd: float
    limit_usd: float
    period_end: str
    over_limit: bool


class UsageResponse(BaseModel):
    instances: list[InstanceUsageResponse]


@router.get("", response_model=UsageResponse)
async def get_usage(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> UsageResponse:
    """Return current month OpenRouter usage (USD) per instance for the authenticated user.

    When OPENROUTER_MANAGEMENT_API_KEY is not set, returns empty usage.
    """
    today = date.today()
    period_end = _period_end_for(today)

    result = await session.execute(
        select(Instance).where(Instance.user_id == user.id).order_by(Instance.created_at.desc())
    )
    instances = result.scalars().all()

    mgmt_key = (getattr(settings, "openrouter_management_api_key", "") or "").strip()
    if not mgmt_key:
        # No OpenRouter Management key configured; return empty usage.
        return UsageResponse(instances=[])

    # Fetch all keys once, then map by name. Keys are created with name "ClawBolt instance <instance_id>".
    keys = openrouter_list_keys(mgmt_key) or []
    keys_by_name: dict[str, dict] = {}
    for k in keys:
        name = k.get("name")
        if isinstance(name, str) and name:
            keys_by_name[name] = k

    default_limit = float(getattr(settings, "openrouter_key_limit_usd", 0) or 0)
    out: list[InstanceUsageResponse] = []

    for inst in instances:
        key_name = f"ClawBolt instance {inst.id}"
        k = keys_by_name.get(key_name)
        if not k:
            continue
        # OpenRouter key fields: limit, limit_remaining, usage_monthly, usage
        usage_monthly = float(k.get("usage_monthly") or k.get("usage") or 0.0)
        limit = float(k.get("limit") or default_limit or 0.0)
        over_limit = bool(limit and usage_monthly >= limit)

        out.append(
            InstanceUsageResponse(
                instance_id=str(inst.id),
                domain=inst.domain,
                used_usd=usage_monthly,
                limit_usd=limit,
                period_end=period_end.isoformat(),
                over_limit=over_limit,
            )
        )

    return UsageResponse(instances=out)
