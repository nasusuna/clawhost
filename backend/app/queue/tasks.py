"""ARQ tasks: provisioning job."""
import asyncio
import base64
import json
import os
import secrets
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import GeminiKeyPool, Instance, InstanceStatus, Subscription, User
from app.db.session import async_session_maker
from app.dns.cloudflare import create_a_record
from app.email.send import send_provisioning_done
from app.gemini_pool.gcp import create_and_store_one_gemini_key, get_available_pool_count
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


def _openclaw_gemini_config_json() -> str:
    """Minimal OpenClaw config: Gemini as default model; API key from env GEMINI_API_KEY."""
    config = {
        "gateway": {
            "port": 18789,
            "mode": "local",
            "bind": "lan",
            "controlUi": {"dangerouslyDisableDeviceAuth": True},
            "auth": {"mode": "token", "token": "__OPENCLAW_REDACTED__"},
            "trustedProxies": ["127.0.0.1", "::1"],
            "tls": {"enabled": False},
        },
        "agents": {
            "defaults": {
                "model": {"primary": "google/gemini-2.5-flash-lite"},
                "workspace": "/home/node/.openclaw/workspace",
                "timeoutSeconds": 1200,
                "maxConcurrent": 4,
            }
        },
        "models": {
            "providers": {
                "google": {
                    "baseUrl": "https://generativelanguage.googleapis.com/v1beta",
                    "models": [
                        {
                            "id": "gemini-2.5-flash-lite",
                            "name": "Gemini 2.5 Flash Lite",
                            "contextWindow": 1048576,
                            "maxTokens": 65536,
                        }
                    ],
                }
            }
        },
    }
    return json.dumps(config, separators=(",", ":"))


def _cloud_init_user_data(
    domain: str,
    gateway_token: str,
    gemini_api_key: str | None = None,
) -> str:
    """Cloud-Init YAML: Docker, OpenClaw with Gemini config, Nginx, Certbot. No Ollama."""
    image = settings.openclaw_docker_image
    port = settings.openclaw_app_port
    openclaw_json = _openclaw_gemini_config_json()

    # Escape gateway_token for shell (single-quote wrap: ' -> '\'')
    gate_esc = gateway_token.replace("'", "'\"'\"'")

    write_files = f"""  - path: /etc/nginx/sites-available/openclaw
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
  - path: /root/openclaw.json
    content: |
      {openclaw_json}
"""
    if gemini_api_key:
        gemini_b64 = base64.b64encode(gemini_api_key.encode()).decode()
        write_files += f"""  - path: /root/gemini_key.b64
    content: |
      {gemini_b64}
"""
    if not gemini_api_key:
        runcmd = f"""
  - curl -fsSL https://get.docker.com | sh
  - apt-get update && apt-get install -y nginx certbot python3-certbot-nginx
  - chmod 666 /root/openclaw.json
  - docker run -d --restart always --name openclaw -p 127.0.0.1:{port}:18789 -v /root/openclaw.json:/home/node/.openclaw/openclaw.json -e OPENCLAW_GATEWAY_TOKEN='{gate_esc}' --security-opt no-new-privileges --cpus=2 --memory=4g {image}
"""
    else:
        runcmd = f"""
  - curl -fsSL https://get.docker.com | sh
  - apt-get update && apt-get install -y nginx certbot python3-certbot-nginx
  - chmod 666 /root/openclaw.json
  - bash -c 'GEMINI_API_KEY=$(base64 -d /root/gemini_key.b64 2>/dev/null || true); docker run -d --restart always --name openclaw -p 127.0.0.1:{port}:18789 -v /root/openclaw.json:/home/node/.openclaw/openclaw.json -e OPENCLAW_GATEWAY_TOKEN=\\'{gate_esc}\\' -e GEMINI_API_KEY="$GEMINI_API_KEY" --security-opt no-new-privileges --cpus=2 --memory=4g {image}'
"""
    return f"""#cloud-config
package_update: true
package_upgrade: true
write_files:
{write_files}
runcmd:
{runcmd}
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
        gemini_api_key = (instance.gemini_api_key or settings.gemini_api_key or "").strip() or None

    # If no user/shared key, assign one from the pool (if any available)
    if not gemini_api_key:
        async with async_session_maker() as session:
            pool_row = await session.execute(
                select(GeminiKeyPool)
                .where(GeminiKeyPool.instance_id.is_(None))
                .with_for_update(skip_locked=True)
                .limit(1)
            )
            row = pool_row.scalar_one_or_none()
            if row:
                row.instance_id = instance_id
                session.add(row)
                await session.commit()
                gemini_api_key = row.api_key

    provider = await _get_provider_client()
    if not provider:
        async with async_session_maker() as session:
            r = await session.execute(select(Instance).where(Instance.id == instance_id))
            inst = r.scalar_one_or_none()
            if inst:
                inst.status = InstanceStatus.stopped
                await session.commit()
        return

    cloud_init = _cloud_init_user_data(domain, gateway_token, gemini_api_key)
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


def _gcp_project_id() -> str | None:
    """Resolve GCP project ID from config or env."""
    return (
        (settings.gcp_project_id or "").strip()
        or os.environ.get("GOOGLE_CLOUD_PROJECT")
        or os.environ.get("GCP_PROJECT_ID")
        or None
    )


async def replenish_gemini_key_pool(_: Any) -> None:
    """ARQ cron: ensure pool has at least gemini_key_pool_min_available unassigned keys by creating via GCP."""
    if not settings.gemini_key_pool_replenish_enabled:
        return
    project_id = _gcp_project_id()
    if not project_id:
        return
    min_available = max(0, settings.gemini_key_pool_min_available)
    # Cap creations per run to avoid rate limits (e.g. 120/min for API Keys API)
    max_create_per_run = 5
    for _ in range(max_create_per_run):
        available = await get_available_pool_count()
        if available >= min_available:
            break
        ok = await create_and_store_one_gemini_key(project_id)
        if not ok:
            break
        await asyncio.sleep(2)
