"""Stripe webhook handler: checkout.session.completed, invoice.payment_failed, customer.subscription.deleted."""
import uuid

import stripe
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import Instance, InstanceStatus, Subscription, SubscriptionStatus, User
from app.email.send import send_payment_failed, send_subscription_canceled
from app.provider.contabo import ContaboClient
from app.queue.worker import enqueue_provision_job

stripe.api_key = settings.stripe_secret_key


async def handle_checkout_session_completed(session: AsyncSession, event: dict) -> None:
    data = event["data"]["object"]
    customer_email = data.get("customer_email") or data.get("customer_details", {}).get("email")
    stripe_subscription_id = data.get("subscription")
    metadata = data.get("metadata") or {}
    user_id_str = metadata.get("user_id")
    plan_type = metadata.get("plan_type", "starter")

    if not user_id_str or not stripe_subscription_id:
        return

    user_id = uuid.UUID(user_id_str)
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return

    # Subscription record
    sub_obj = stripe.Subscription.retrieve(stripe_subscription_id)
    current_period_end = None
    if sub_obj.current_period_end:
        from datetime import datetime, timezone
        current_period_end = datetime.fromtimestamp(sub_obj.current_period_end, tz=timezone.utc)

    subscription = Subscription(
        user_id=user_id,
        stripe_subscription_id=stripe_subscription_id,
        status=SubscriptionStatus.active,
        plan_type=plan_type,
        current_period_end=current_period_end,
    )
    session.add(subscription)
    await session.flush()
    await session.refresh(subscription)

    # Instance row (provisioning); commit so worker sees it, then enqueue
    instance = Instance(
        user_id=user_id,
        subscription_id=subscription.id,
        status=InstanceStatus.provisioning,
        provision_job_id=None,
    )
    session.add(instance)
    await session.commit()
    await enqueue_provision_job(user_id, subscription.id, plan_type)


async def handle_invoice_payment_failed(session: AsyncSession, event: dict) -> None:
    data = event["data"]["object"]
    stripe_subscription_id = data.get("subscription")
    if not stripe_subscription_id:
        return
    result = await session.execute(
        select(Subscription).where(Subscription.stripe_subscription_id == stripe_subscription_id)
    )
    subscription = result.scalar_one_or_none()
    if not subscription:
        return
    subscription.status = SubscriptionStatus.past_due
    session.add(subscription)

    instances_result = await session.execute(
        select(Instance).where(
            and_(Instance.subscription_id == subscription.id, Instance.status == InstanceStatus.running)
        )
    )
    instances = list(instances_result.scalars().all())
    provider = None
    if all([
        settings.contabo_api_url,
        settings.contabo_client_id,
        settings.contabo_client_secret,
        settings.contabo_api_user,
        settings.contabo_api_password,
    ]):
        provider = ContaboClient(settings.contabo_api_url)
    user_result = await session.execute(select(User).where(User.id == subscription.user_id))
    user = user_result.scalar_one_or_none()

    for inst in instances:
        inst.status = InstanceStatus.stopped
        session.add(inst)
        if provider and inst.provider_vps_id:
            try:
                await provider.power_off(inst.provider_vps_id)
            except NotImplementedError:
                pass
    if user:
        await send_payment_failed(user.email)


async def handle_subscription_deleted(session: AsyncSession, event: dict) -> None:
    data = event["data"]["object"]
    stripe_subscription_id = data.get("id")
    if not stripe_subscription_id:
        return
    result = await session.execute(
        select(Subscription).where(Subscription.stripe_subscription_id == stripe_subscription_id)
    )
    subscription = result.scalar_one_or_none()
    if not subscription:
        return
    subscription.status = SubscriptionStatus.canceled
    session.add(subscription)

    instances_result = await session.execute(
        select(Instance).where(Instance.subscription_id == subscription.id)
    )
    instances = list(instances_result.scalars().all())
    provider = None
    if all([
        settings.contabo_api_url,
        settings.contabo_client_id,
        settings.contabo_client_secret,
        settings.contabo_api_user,
        settings.contabo_api_password,
    ]):
        provider = ContaboClient(settings.contabo_api_url)
    user_result = await session.execute(select(User).where(User.id == subscription.user_id))
    user = user_result.scalar_one_or_none()

    for inst in instances:
        inst.status = InstanceStatus.deleted
        session.add(inst)
        if provider and inst.provider_vps_id:
            try:
                await provider.delete(inst.provider_vps_id)
            except NotImplementedError:
                pass
    if user:
        await send_subscription_canceled(user.email)
