"""Instance routes: list, get one, retry provisioning."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.auth.deps import get_current_user
from app.db.models import Instance, InstanceStatus, Subscription, User
from app.db.session import get_session
from app.instances.schemas import InstanceResponse, InstanceUpdate
from app.queue.worker import enqueue_provision_job
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/instances", tags=["instances"])


@router.get("", response_model=list[InstanceResponse])
async def list_instances(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[InstanceResponse]:
    result = await session.execute(select(Instance).where(Instance.user_id == user.id).order_by(Instance.created_at.desc()))
    instances = result.scalars().all()
    return [
        InstanceResponse(
            id=str(i.id),
            status=i.status.value,
            domain=i.domain,
            ip_address=i.ip_address,
            gateway_token=i.gateway_token,
            gemini_api_key_set=bool(i.gemini_api_key),
            created_at=i.created_at,
            last_heartbeat=i.last_heartbeat,
        )
        for i in instances
    ]


@router.get("/{instance_id}", response_model=InstanceResponse)
async def get_instance(
    instance_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> InstanceResponse:
    result = await session.execute(
        select(Instance).where(Instance.id == instance_id, Instance.user_id == user.id)
    )
    instance = result.scalar_one_or_none()
    if not instance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Instance not found")
    return InstanceResponse(
        id=str(instance.id),
        status=instance.status.value,
        domain=instance.domain,
        ip_address=instance.ip_address,
        gateway_token=instance.gateway_token,
        gemini_api_key_set=bool(instance.gemini_api_key),
        created_at=instance.created_at,
        last_heartbeat=instance.last_heartbeat,
    )


@router.patch("/{instance_id}", response_model=InstanceResponse)
async def update_instance(
    instance_id: UUID,
    body: InstanceUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> InstanceResponse:
    """Update instance (e.g. set Gemini API key). Key is used on next provision or can be synced later."""
    result = await session.execute(
        select(Instance).where(Instance.id == instance_id, Instance.user_id == user.id)
    )
    instance = result.scalar_one_or_none()
    if not instance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Instance not found")
    if body.gemini_api_key is not None:
        instance.gemini_api_key = body.gemini_api_key.strip() or None
    session.add(instance)
    await session.commit()
    await session.refresh(instance)
    return InstanceResponse(
        id=str(instance.id),
        status=instance.status.value,
        domain=instance.domain,
        ip_address=instance.ip_address,
        gateway_token=instance.gateway_token,
        gemini_api_key_set=bool(instance.gemini_api_key),
        created_at=instance.created_at,
        last_heartbeat=instance.last_heartbeat,
    )


@router.post("/{instance_id}/retry-provisioning")
async def retry_provisioning(
    instance_id: UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Re-enqueue provisioning job for an instance stuck in provisioning."""
    result = await session.execute(
        select(Instance).where(Instance.id == instance_id, Instance.user_id == user.id)
    )
    instance = result.scalar_one_or_none()
    if not instance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Instance not found")
    if instance.status != InstanceStatus.provisioning:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Instance is not in provisioning state",
        )
    if not instance.subscription_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Instance has no subscription",
        )
    sub_result = await session.execute(
        select(Subscription).where(Subscription.id == instance.subscription_id)
    )
    subscription = sub_result.scalar_one_or_none()
    if not subscription:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Subscription not found")
    await enqueue_provision_job(user.id, instance.subscription_id, subscription.plan_type)
    return {"ok": True, "message": "Provisioning job enqueued. Worker will process it shortly."}
