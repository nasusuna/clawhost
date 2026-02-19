"""Cloudflare API: create A record for instance subdomain."""
from app.config import settings


async def create_a_record(subdomain: str, ip_address: str) -> None:
    """Create or update A record: subdomain -> IP. Uses CLAWHOST_BASE_DOMAIN."""
    # TODO: Use Cloudflare API (zone_id, token) to create A record
    # Example: POST /zones/{zone_id}/dns_records { "type": "A", "name": subdomain, "content": ip_address }
    if not settings.cloudflare_api_token or not settings.cloudflare_zone_id:
        return
    # Placeholder: implement with httpx
    _ = subdomain, ip_address
