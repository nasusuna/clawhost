"""ARQ tasks: provisioning job."""
import asyncio
import secrets
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import Instance, InstanceStatus, Subscription, User
from app.db.session import async_session_maker
from app.dns.cloudflare import create_a_record
from app.email.send import send_provisioning_done
from app.provider.contabo import ContaboClient


async def _get_provider_client() -> ContaboClient | None:
    if not all([
        settings.contabo_api_url,
        settings.contabo_client_id,
        settings.contabo_client_secret,
        settings.contabo_api_user,
        settings.contabo_api_password,
    ]):
        return None
    return ContaboClient(settings.contabo_api_url)


def _cloud_init_user_data(domain: str, gateway_token: str) -> str:
    """Cloud-Init YAML: Docker, OpenClaw on localhost, Nginx reverse proxy on 80, Certbot."""
    image = settings.openclaw_docker_image
    port = settings.openclaw_app_port
    # Nginx on 80 proxies to OpenClaw container on 127.0.0.1:port
    return f"""#cloud-config
package_update: true
package_upgrade: true
write_files:
  - path: /etc/nginx/sites-available/openclaw
    content: |
      server {{
        listen 80;
        server_name {domain};
        location / {{
          proxy_pass http://127.0.0.1:{port};
          proxy_http_version 1.1;
          proxy_set_header Host $host;
          proxy_set_header X-Real-IP $remote_addr;
          proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
          proxy_set_header X-Forwarded-Proto $scheme;
          proxy_set_header Upgrade $http_upgrade;
          proxy_set_header Connection "upgrade";
          proxy_read_timeout 86400;
        }}
      }}
runcmd:
  - curl -fsSL https://get.docker.com | sh
  - docker run -d --restart always -p 127.0.0.1:{port}:{port} --name openclaw -e OPENCLAW_GATEWAY_TOKEN='{gateway_token}' --security-opt no-new-privileges --cpus=2 --memory=4g {image}
  - apt-get update && apt-get install -y nginx certbot python3-certbot-nginx
  - rm -f /etc/nginx/sites-enabled/default
  - ln -sf /etc/nginx/sites-available/openclaw /etc/nginx/sites-enabled/openclaw
  - systemctl enable nginx
  - systemctl start nginx
  - certbot --nginx -d {domain} --non-interactive --agree-tos --email admin@{domain} --redirect
"""


async def provision_instance(
    ctx: dict[str, Any],
    user_id_str: str,
    subscription_id_str: str,
    plan_type: str,
) -> None:
    """ARQ job: create VPS, poll until ready, DNS, update instance, email."""
    user_id = uuid.UUID(user_id_str)
    subscription_id = uuid.UUID(subscription_id_str)
    job_id = ctx.get("job_id", "unknown")

    async with async_session_maker() as session:
        result = await session.execute(
            select(User, Subscription).join(Subscription, Subscription.user_id == User.id).where(
                User.id == user_id, Subscription.id == subscription_id
            )
        )
        row = result.one_or_none()
        if not row:
            return
        user, subscription = row

        # Instance created by webhook; find it and set domain + job_id
        inst_result = await session.execute(
            select(Instance).where(
                and_(
                    Instance.subscription_id == subscription_id,
                    Instance.status == InstanceStatus.provisioning,
                )
            )
        )
        instance = inst_result.scalar_one_or_none()
        if not instance:
            return
        domain = f"{user_id.hex[:12]}.{settings.clawhost_base_domain}"
        gateway_token = secrets.token_urlsafe(32)
        instance.domain = domain
        instance.gateway_token = gateway_token
        instance.provision_job_id = job_id
        session.add(instance)
        await session.commit()
        instance_id = instance.id

    provider = await _get_provider_client()
    if not provider:
        async with async_session_maker() as session:
            r = await session.execute(select(Instance).where(Instance.id == instance_id))
            inst = r.scalar_one_or_none()
            if inst:
                inst.status = InstanceStatus.stopped
                await session.commit()
        return

    cloud_init = _cloud_init_user_data(domain, gateway_token)
    try:
        create_result = await provider.create_vps(
            region="default",
            plan_type=plan_type,
            cloud_init_user_data=cloud_init,
        )
    except (NotImplementedError, RuntimeError, Exception):
        async with async_session_maker() as session:
            r = await session.execute(select(Instance).where(Instance.id == instance_id))
            inst = r.scalar_one_or_none()
            if inst:
                inst.status = InstanceStatus.stopped
                await session.commit()
        return

    async with async_session_maker() as session:
        r = await session.execute(select(Instance).where(Instance.id == instance_id))
        inst = r.scalar_one()
        inst.provider_vps_id = create_result.provider_vps_id
        inst.ip_address = create_result.ip_address
        inst.root_password = create_result.root_password
        await session.commit()

    # Poll until running (60s interval, max 30)
    for attempt in range(30):
        await asyncio.sleep(60)
        status = await provider.get_status(create_result.provider_vps_id)
        if status == "running":
            break
        if status in ("deleted", "error"):
            async with async_session_maker() as session:
                r = await session.execute(select(Instance).where(Instance.id == instance_id))
                inst = r.scalar_one_or_none()
                if inst:
                    inst.status = InstanceStatus.stopped
                    await session.commit()
            return

    # Get IP (create response often has no IP; get_instance returns it when running)
    ip_address = create_result.ip_address or ""
    details = await provider.get_instance(create_result.provider_vps_id)
    if details and details.ip_address:
        ip_address = details.ip_address

    await create_a_record(domain, ip_address)

    now = datetime.now(timezone.utc)
    async with async_session_maker() as session:
        r = await session.execute(select(Instance).where(Instance.id == instance_id))
        inst = r.scalar_one()
        inst.status = InstanceStatus.running
        inst.ip_address = ip_address or inst.ip_address
        inst.last_heartbeat = now
        await session.commit()

    login_url = f"https://{domain}"
    await send_provisioning_done(user.email, login_url, domain, ip_address)
