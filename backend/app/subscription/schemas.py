"""Subscription request/response schemas."""
from datetime import datetime
from pydantic import BaseModel


class PlanInfo(BaseModel):
    id: str
    name: str
    vcpu: int
    memory_gb: int


class SubscriptionResponse(BaseModel):
    id: str
    status: str
    plan_type: str
    current_period_end: datetime | None

    class Config:
        from_attributes = True


class CreateCheckoutRequest(BaseModel):
    plan_type: str  # starter | pro
    success_url: str
    cancel_url: str
