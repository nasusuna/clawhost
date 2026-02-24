"""Cloudflare API: create or update A record for instance domain."""
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


async def create_a_record(domain: str, ip_address: str) -> None:
    """Create or update A record: domain -> IP so instance is reachable at https://{domain}."""
    if not settings.cloudflare_api_token or not settings.cloudflare_zone_id:
        logger.warning("create_a_record: CLOUDFLARE_API_TOKEN or CLOUDFLARE_ZONE_ID not set; skipping DNS")
        return
    if not domain or not ip_address:
        return
    zone_id = settings.cloudflare_zone_id.strip()
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
    headers = {"Authorization": f"Bearer {settings.cloudflare_api_token.strip()}", "Content-Type": "application/json"}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # List existing A record for this name so we can update instead of duplicate
            list_resp = await client.get(url, params={"name": domain, "type": "A"}, headers=headers)
            list_resp.raise_for_status()
            data = list_resp.json()
            records = (data.get("result") or []) if data.get("success") else []

            body = {"type": "A", "name": domain, "content": ip_address, "ttl": 1}
            if records:
                record_id = records[0]["id"]
                patch_url = f"{url}/{record_id}"
                resp = await client.patch(patch_url, json=body, headers=headers)
                if not resp.json().get("success"):
                    logger.warning("create_a_record: Cloudflare PATCH failed domain=%s: %s", domain, resp.text)
                else:
                    logger.info("create_a_record: updated A record domain=%s -> %s", domain, ip_address)
            else:
                resp = await client.post(url, json=body, headers=headers)
                if not resp.json().get("success"):
                    logger.warning("create_a_record: Cloudflare POST failed domain=%s: %s", domain, resp.text)
                else:
                    logger.info("create_a_record: created A record domain=%s -> %s", domain, ip_address)
    except Exception as e:
        logger.warning("create_a_record: failed domain=%s: %s", domain, e)
