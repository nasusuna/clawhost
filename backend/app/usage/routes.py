"""Usage routes: current user's Gemini token usage per instance (for dashboard)."""
import calendar
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select

from app.auth.deps import get_current_user
from app.db.models import Instance, GeminiUsage, User
from app.db.session import get_session
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/usage", tags=["usage"])

# Monthly token cap per instance (~$15/month equivalent for Gemini 2.5 Flash-Lite)
TOKENS_CAP_PER_MONTH = 60_000_000


def _period_start_for(d: date) -> date:
    """First day of the month for the given date."""
    return date(d.year, d.month, 1)


def _period_end_for(d: date) -> date:
    """Last day of the month."""
    _, last = calendar.monthrange(d.year, d.month)
    return date(d.year, d.month, last)


class InstanceUsageResponse(BaseModel):
    instance_id: str
    domain: str | None
    tokens_used: int
    tokens_cap: int
    period_end: str
    over_limit: bool


class UsageResponse(BaseModel):
    instances: list[InstanceUsageResponse]


@router.get("", response_model=UsageResponse)
async def get_usage(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> UsageResponse:
    """Return current month Gemini token usage per instance for the authenticated user."""
    today = date.today()
    period_start = _period_start_for(today)
    period_end = _period_end_for(today)

    result = await session.execute(
        select(Instance).where(Instance.user_id == user.id).order_by(Instance.created_at.desc())
    )
    instances = result.scalars().all()
    out: list[InstanceUsageResponse] = []

    for inst in instances:
        usage_result = await session.execute(
            select(GeminiUsage).where(
                GeminiUsage.instance_id == inst.id,
                GeminiUsage.period_start == period_start,
            )
        )
        row = usage_result.scalar_one_or_none()
        tokens_used = int(row.tokens_used) if row else 0
        over_limit = tokens_used >= TOKENS_CAP_PER_MONTH

        out.append(
            InstanceUsageResponse(
                instance_id=str(inst.id),
                domain=inst.domain,
                tokens_used=tokens_used,
                tokens_cap=TOKENS_CAP_PER_MONTH,
                period_end=period_end.isoformat(),
                over_limit=over_limit,
            )
        )

    return UsageResponse(instances=out)
