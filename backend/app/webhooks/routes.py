"""Stripe webhook route: POST /webhooks/stripe."""
from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

import stripe
from app.config import settings
from app.db.session import get_session
from app.webhooks.stripe_handler import (
    handle_checkout_session_completed,
    handle_invoice_payment_failed,
    handle_subscription_deleted,
)

router = APIRouter(tags=["webhooks"])


@router.post("/webhooks/stripe")
async def stripe_webhook(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> dict:
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    if not settings.stripe_webhook_secret:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Webhook secret not configured")
    try:
        event = stripe.Webhook.construct_event(payload, sig, settings.stripe_webhook_secret)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payload")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if event["type"] == "checkout.session.completed":
        await handle_checkout_session_completed(session, event)
    elif event["type"] == "invoice.payment_failed":
        await handle_invoice_payment_failed(session, event)
    elif event["type"] == "customer.subscription.deleted":
        await handle_subscription_deleted(session, event)

    return {"received": True}
