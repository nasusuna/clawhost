"""Subscription plan definitions and Stripe price mapping."""
from app.config import settings

PLAN_STARTER = "starter"
PLAN_PRO = "pro"

PLANS = {
    PLAN_STARTER: {
        "name": "Starter",
        "vcpu": 2,
        "memory_gb": 4,
        "stripe_price_id_key": "stripe_starter_price_id",
    },
    PLAN_PRO: {
        "name": "Pro",
        "vcpu": 2,
        "memory_gb": 8,
        "stripe_price_id_key": "stripe_pro_price_id",
    },
}


def get_stripe_price_id(plan_type: str) -> str | None:
    plan = PLANS.get(plan_type)
    if not plan:
        return None
    return getattr(settings, plan["stripe_price_id_key"], None) or ""
