"""Subscription routes: list plans, create Stripe Checkout session."""
import stripe
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user
from app.config import settings
from app.db.models import User
from app.db.session import get_session
from app.subscription.plans import PLANS, PLAN_PRO, PLAN_STARTER
from sqlalchemy import select

from app.subscription.schemas import CreateCheckoutRequest, PlanInfo, SubscriptionResponse
from app.subscription.service import create_checkout_session
from app.db.models import Subscription, SubscriptionStatus

router = APIRouter(prefix="/subscription", tags=["subscription"])


@router.get("/plans", response_model=list[PlanInfo])
async def list_plans() -> list[PlanInfo]:
    return [
        PlanInfo(id=PLAN_STARTER, name=PLANS[PLAN_STARTER]["name"], vcpu=PLANS[PLAN_STARTER]["vcpu"], memory_gb=PLANS[PLAN_STARTER]["memory_gb"]),
        PlanInfo(id=PLAN_PRO, name=PLANS[PLAN_PRO]["name"], vcpu=PLANS[PLAN_PRO]["vcpu"], memory_gb=PLANS[PLAN_PRO]["memory_gb"]),
    ]


@router.get("/me", response_model=SubscriptionResponse | None)
async def get_my_subscription(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> SubscriptionResponse | None:
    result = await session.execute(
        select(Subscription)
        .where(Subscription.user_id == user.id, Subscription.status == SubscriptionStatus.active)
        .order_by(Subscription.created_at.desc())
        .limit(1)
    )
    sub = result.scalar_one_or_none()
    if not sub:
        return None
    return SubscriptionResponse(
        id=str(sub.id),
        status=sub.status.value,
        plan_type=sub.plan_type,
        current_period_end=sub.current_period_end,
    )


@router.post("/checkout")
async def checkout(
    body: CreateCheckoutRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    if body.plan_type not in PLANS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid plan_type")
    if not settings.stripe_secret_key:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Stripe not configured")
    try:
        url = await create_checkout_session(
            session=session,
            user=user,
            plan_type=body.plan_type,
            success_url=body.success_url,
            cancel_url=body.cancel_url,
        )
    except stripe.error.InvalidRequestError as e:
        msg = str(e).strip()
        if "No such price" in msg or "resource_missing" in getattr(e, "code", ""):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "Stripe price ID is invalid or missing. In Stripe Dashboard use a price ID (price_...), "
                    "not a product ID (prod_...). Product → Pricing → copy the price ID. "
                    "Set STRIPE_STARTER_PRICE_ID and STRIPE_PRO_PRICE_ID in Railway."
                ),
            ) from e
        if "product is not active" in msg.lower() or "not available to be purchased" in msg.lower():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "This plan is not available for purchase: the product is not active in Stripe. "
                    "In Stripe Dashboard → Product catalogue → open the product → set status to Active (or unarchive it)."
                ),
            ) from e
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Stripe request failed") from e
    return {"checkout_url": url}
