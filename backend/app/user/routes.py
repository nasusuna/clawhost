"""User profile routes: optional Telegram bot token for OpenClaw."""
import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user
from app.db.models import Instance, InstanceStatus, User
from app.db.session import get_session
from app.queue.tasks import openclaw_config_dict
from app.queue.worker import enqueue_apply_telegram_to_instance

router = APIRouter(prefix="/user", tags=["user"])
logger = logging.getLogger(__name__)


class TelegramTokenPut(BaseModel):
    bot_token: str = ""


class TelegramTokenStatus(BaseModel):
    has_token: bool


class TelegramConfigSnippet(BaseModel):
    """JSON fragment to add to OpenClaw config for existing instances."""

    config_fragment: dict


class TelegramFullConfigInstance(BaseModel):
    """Full OpenClaw config for one instance (copy-paste entire config)."""

    instance_id: str
    domain: str | None
    full_config: dict


class TelegramFullConfigResponse(BaseModel):
    """Per-instance full configs when user has a token and running instances."""

    instances: list[TelegramFullConfigInstance]


async def _validate_telegram_token(token: str) -> bool:
    """Validate token via Telegram Bot API getMe. Returns True if valid."""
    token = (token or "").strip()
    if not token:
        return False
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(f"https://api.telegram.org/bot{token}/getMe")
            data = r.json() if r.content else {}
            return data.get("ok") is True
    except Exception as e:
        logger.warning("Telegram getMe failed: %s", e)
        return False


@router.put("/telegram-token", response_model=TelegramTokenStatus)
async def put_telegram_token(
    body: TelegramTokenPut,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> TelegramTokenStatus:
    """
    Set or clear the user's Telegram bot token (optional step for OpenClaw Telegram channel).
    Token is validated via Telegram Bot API getMe before saving.
    """
    raw = (body.bot_token or "").strip()
    if not raw:
        user.telegram_bot_token = None
        session.add(user)
        await session.commit()
        return TelegramTokenStatus(has_token=False)
    if not await _validate_telegram_token(raw):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Telegram bot token. Check the token with @BotFather and try again.",
        )
    user.telegram_bot_token = raw
    session.add(user)
    await session.commit()

    # Enqueue apply-telegram for each running instance that has IP and root password
    result = await session.execute(
        select(Instance).where(
            and_(
                Instance.user_id == user.id,
                Instance.status == InstanceStatus.running,
                Instance.ip_address.isnot(None),
                Instance.root_password.isnot(None),
            )
        )
    )
    for instance in result.scalars().all():
        try:
            await enqueue_apply_telegram_to_instance(instance.id, user.id)
            logger.info("Enqueued apply_telegram_to_instance instance_id=%s", instance.id)
        except Exception as e:
            logger.warning("Failed to enqueue apply_telegram instance_id=%s: %s", instance.id, e)

    return TelegramTokenStatus(has_token=True)


@router.get("/telegram-token", response_model=TelegramTokenStatus)
async def get_telegram_token_status(
    user: User = Depends(get_current_user),
) -> TelegramTokenStatus:
    """Return whether the user has a Telegram bot token set (never returns the token)."""
    return TelegramTokenStatus(has_token=bool(user.telegram_bot_token and user.telegram_bot_token.strip()))


@router.get("/telegram-config-snippet", response_model=TelegramConfigSnippet | None)
async def get_telegram_config_snippet(
    user: User = Depends(get_current_user),
) -> TelegramConfigSnippet | None:
    """
    Return the OpenClaw channels.telegram config fragment for existing instances.
    User can merge this into their OpenClaw config (Control UI or openclaw.json on the server).
    Returns None if user has no token set.
    """
    token = (user.telegram_bot_token or "").strip()
    if not token:
        return None
    return TelegramConfigSnippet(
        config_fragment={
            "channels": {
                "telegram": {
                    "enabled": True,
                    "botToken": token,
                    "dmPolicy": "pairing",
                    "groups": {"*": {"requireMention": True}},
                }
            }
        }
    )


@router.get("/telegram-full-config", response_model=TelegramFullConfigResponse | None)
async def get_telegram_full_config(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> TelegramFullConfigResponse | None:
    """
    Return full OpenClaw config (per running instance) with Telegram included.
    User can copy-paste the entire JSON into OpenClaw config (replace whole file).
    Returns None if user has no token set.
    """
    token = (user.telegram_bot_token or "").strip()
    if not token:
        return None
    result = await session.execute(
        select(Instance).where(
            and_(
                Instance.user_id == user.id,
                Instance.status == InstanceStatus.running,
            )
        )
    )
    instances = result.scalars().all()
    out = []
    for inst in instances:
        full_config = openclaw_config_dict(
            gateway_token=inst.gateway_token,
            gemini_api_key=inst.gemini_api_key,
            telegram_bot_token=token,
            openrouter_api_key=inst.openrouter_api_key,
        )
        out.append(
            TelegramFullConfigInstance(
                instance_id=str(inst.id),
                domain=inst.domain,
                full_config=full_config,
            )
        )
    return TelegramFullConfigResponse(instances=out) if out else TelegramFullConfigResponse(instances=[])
