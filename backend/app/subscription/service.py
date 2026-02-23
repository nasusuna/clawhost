"""Stripe Checkout session creation."""
from uuid import UUID

import stripe
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import User
from app.subscription.plans import get_stripe_price_id

stripe.api_key = settings.stripe_secret_key


def _ensure_price_id(plan_type: str, value: str) -> str:
    """Ensure the configured value is a Stripe price ID, not a product ID."""
    if not value or not value.strip():
        raise ValueError(f"No Stripe price configured for plan {plan_type}")
    v = value.strip()
    if v.startswith("prod_"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Stripe price ID is incorrect: you set a product ID (prod_...). "
                "Use a price ID (price_...) from Stripe Dashboard → Product → Pricing. "
                "Set STRIPE_STARTER_PRICE_ID and STRIPE_PRO_PRICE_ID to price IDs."
            ),
        )
    if not v.startswith("price_"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe price ID must start with price_. Check STRIPE_STARTER_PRICE_ID and STRIPE_PRO_PRICE_ID.",
        )
    return v


async def create_checkout_session(
    session: AsyncSession,
    user: User,
    plan_type: str,
    success_url: str,
    cancel_url: str,
) -> str:
    price_id = get_stripe_price_id(plan_type)
    if not price_id:
        raise ValueError(f"No Stripe price for plan {plan_type}")
    price_id = _ensure_price_id(plan_type, price_id)
    customer_id = user.stripe_customer_id
    if not customer_id:
        customer = stripe.Customer.create(email=user.email)
        customer_id = customer.id
        user.stripe_customer_id = customer_id
        session.add(user)
        await session.flush()
    checkout_session = stripe.checkout.Session.create(
        customer=customer_id,
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"user_id": str(user.id), "plan_type": plan_type},
    )
    return checkout_session.url or ""
