"""Contabo API client — create VPS, get status, stop, cancel."""
import uuid
from typing import Any

import httpx

from app.provider.base import CreateVpsResult, InstanceDetails, ProviderClient
from app.provider.contabo_auth import get_contabo_token

# Ubuntu 22.04 (Contabo default image)
DEFAULT_IMAGE_ID = "afecbb85-e2fc-46f0-9684-b46b1faf00bb"

# plan_type -> Contabo productId (VPS 10 SSD, VPS 20 SSD)
PRODUCT_IDS: dict[str, str] = {
    "starter": "V92",  # VPS 10 SSD, 150 GB
    "pro": "V95",       # VPS 20 SSD, 200 GB
}

# API status -> our normalized status
STATUS_MAP = {
    "running": "running",
    "provisioning": "pending",
    "installing": "pending",
    "manual_provisioning": "pending",
    "stopped": "stopped",
    "uninstalled": "deleted",
    "error": "error",
    "unknown": "pending",
    "rescue": "stopped",
    "pending_payment": "pending",
    "other": "pending",
}


class ContaboClient(ProviderClient):
    """Contabo VPS API via OAuth2 and REST. Auth from settings (get_contabo_token)."""

    def __init__(self, api_url: str) -> None:
        self.api_url = api_url.rstrip("/")

    def _headers(self, token: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "x-request-id": str(uuid.uuid4()),
        }

    async def _token(self) -> str | None:
        return await get_contabo_token()

    async def create_vps(
        self,
        region: str,
        plan_type: str,
        cloud_init_user_data: str,
        root_password: str | None = None,
    ) -> CreateVpsResult:
        token = await self._token()
        if not token:
            raise RuntimeError("Contabo: no OAuth token")
        product_id = PRODUCT_IDS.get(plan_type, "V92")
        # Contabo regions: EU, US-central, US-east, US-west, SIN, UK, AUS, JPN, IND
        region_val = "EU" if region == "default" else region
        body: dict[str, Any] = {
            "imageId": DEFAULT_IMAGE_ID,
            "productId": product_id,
            "region": region_val,
            "userData": cloud_init_user_data,
            "period": 1,
        }
        if root_password:
            # Optional: use Secrets API to create password secret and set body["rootPassword"] = secret_id
            pass
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{self.api_url}/v1/compute/instances",
                json=body,
                headers=self._headers(token),
            )
        if resp.status_code not in (200, 201):
            raise RuntimeError(f"Contabo create_vps failed: {resp.status_code} {resp.text}")
        data = resp.json()
        items = data.get("data") or []
        if not items:
            raise RuntimeError("Contabo create_vps: no data in response")
        instance_id = items[0].get("instanceId")
        if instance_id is None:
            raise RuntimeError("Contabo create_vps: no instanceId")
        # IP may not be present until instance is running; worker will get it via get_instance
        ip = ""
        if isinstance(items[0], dict):
            ip_cfg = (items[0].get("ipConfig") or {}).get("v4") or {}
            ip = ip_cfg.get("ip") or ""
        return CreateVpsResult(
            provider_vps_id=str(instance_id),
            ip_address=ip,
            root_password=root_password,
        )

    async def get_status(self, provider_vps_id: str) -> str:
        details = await self.get_instance(provider_vps_id)
        return details.status if details else "deleted"

    async def get_instance(self, provider_vps_id: str) -> InstanceDetails | None:
        token = await self._token()
        if not token:
            return None
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{self.api_url}/v1/compute/instances/{provider_vps_id}",
                headers=self._headers(token),
            )
        if resp.status_code != 200:
            return None
        data = resp.json()
        items = data.get("data") or []
        if not items:
            return None
        obj = items[0] if isinstance(items[0], dict) else {}
        raw_status = (obj.get("status") or "unknown").lower()
        status = STATUS_MAP.get(raw_status, "pending")
        ip_cfg = obj.get("ipConfig") or {}
        v4 = ip_cfg.get("v4") or {}
        ip_address = v4.get("ip") or None
        return InstanceDetails(status=status, ip_address=ip_address)

    async def power_off(self, provider_vps_id: str) -> None:
        token = await self._token()
        if not token:
            raise RuntimeError("Contabo: no OAuth token")
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self.api_url}/v1/compute/instances/{provider_vps_id}/actions/stop",
                headers=self._headers(token),
            )
        if resp.status_code not in (200, 202, 204):
            raise RuntimeError(f"Contabo power_off failed: {resp.status_code} {resp.text}")

    async def delete(self, provider_vps_id: str) -> None:
        token = await self._token()
        if not token:
            raise RuntimeError("Contabo: no OAuth token")
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self.api_url}/v1/compute/instances/{provider_vps_id}/cancel",
                headers=self._headers(token),
            )
        if resp.status_code not in (200, 202, 204):
            raise RuntimeError(f"Contabo delete/cancel failed: {resp.status_code} {resp.text}")
