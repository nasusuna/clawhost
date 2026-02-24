"""Auth routes: register, login, delete account."""
import logging

import stripe
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user
from app.auth.jwt import create_access_token
from app.auth.password import hash_password, verify_password
from app.auth.schemas import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.config import settings
from app.db.models import Instance, Subscription, User
from app.db.session import get_session

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


@router.post("/register", response_model=TokenResponse)
async def register(
    body: RegisterRequest,
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    result = await session.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
    )
    session.add(user)
    await session.flush()
    await session.refresh(user)
    token = create_access_token(user.id)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    result = await session.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    token = create_access_token(user.id)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse(id=str(user.id), email=user.email)


@router.delete("/account")
async def delete_account(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """
    Permanently delete the current user account: cancel Stripe subscriptions,
    cancel Contabo VPS for all instances, then delete user and all related data.
    """
    user_id = user.id

    # Cancel Stripe subscriptions so the customer is not charged further
    if settings.stripe_secret_key:
        subs_result = await session.execute(select(Subscription).where(Subscription.user_id == user_id))
        for sub in subs_result.scalars().all():
            try:
                stripe.Subscription.delete(sub.stripe_subscription_id)
                logger.info("Canceled Stripe subscription %s for account deletion", sub.stripe_subscription_id)
            except stripe.error.StripeError as e:
                logger.warning("Failed to cancel Stripe subscription %s: %s", sub.stripe_subscription_id, e)

    # Cancel Contabo VPS for all instances so we don't leave orphaned VPS
    contabo_configured = all([
        settings.contabo_api_url,
        settings.contabo_client_id,
        settings.contabo_client_secret,
        settings.contabo_api_user,
        settings.contabo_api_password,
    ])
    if contabo_configured:
        from app.provider.contabo import ContaboClient
        provider = ContaboClient(settings.contabo_api_url)
        instances_result = await session.execute(select(Instance).where(Instance.user_id == user_id))
        for inst in instances_result.scalars().all():
            if inst.provider_vps_id:
                try:
                    await provider.delete(inst.provider_vps_id)
                    logger.info("Canceled Contabo VPS %s for account deletion", inst.provider_vps_id)
                except Exception as e:
                    logger.warning("Failed to cancel Contabo VPS %s: %s", inst.provider_vps_id, e)

    await session.delete(user)
    await session.commit()
    logger.info("Deleted account user_id=%s email=%s", user_id, user.email)
    return {"ok": True, "message": "Account deleted"}
