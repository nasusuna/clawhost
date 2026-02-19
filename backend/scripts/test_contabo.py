"""
Test Contabo OAuth and API (read-only).
From backend dir with venv activated:
  python scripts/test_contabo.py
Or: uv run python scripts/test_contabo.py
"""
import asyncio
import sys

# Load app config (needs backend on path)
sys.path.insert(0, ".")

from app.config import settings
from app.provider.contabo_auth import get_contabo_token


async def main() -> None:
    print("Checking Contabo env vars...")
    required = [
        ("CONTABO_API_URL", settings.contabo_api_url),
        ("CONTABO_CLIENT_ID", settings.contabo_client_id),
        ("CONTABO_CLIENT_SECRET", "***" if settings.contabo_client_secret else ""),
        ("CONTABO_API_USER", settings.contabo_api_user),
        ("CONTABO_API_PASSWORD", "***" if settings.contabo_api_password else ""),
    ]
    for name, val in required:
        ok = "ok" if (val and (name.endswith("PASSWORD") or name.endswith("SECRET") or len(str(val)) > 2)) else "missing"
        if "SECRET" in name or "PASSWORD" in name:
            print(f"  {name}: {'set' if val else 'missing'}")
        else:
            print(f"  {name}: {val or 'missing'}")

    if not all([
        settings.contabo_api_url,
        settings.contabo_client_id,
        settings.contabo_client_secret,
        settings.contabo_api_user,
        settings.contabo_api_password,
    ]):
        print("\nAdd all Contabo variables to .env and run again.")
        return

    print("\n1. Fetching OAuth token...")
    token = await get_contabo_token()
    if not token:
        print("   FAILED: No token (check client id/secret and API user/password).")
        return
    print("   OK: Token received.")

    print("\n2. Listing compute instances (GET /v1/compute/instances)...")
    import httpx
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "x-request-id": "00000000-0000-0000-0000-000000000001",
    }
    async with httpx.AsyncClient(timeout=30.0) as http_client:
        resp = await http_client.get(
            f"{settings.contabo_api_url}/v1/compute/instances?size=1",
            headers=headers,
        )
    if resp.status_code == 200:
        data = resp.json()
        total = data.get("_pagination", {}).get("totalElements", 0)
        print(f"   OK: API responded. You have {total} instance(s).")
    else:
        print(f"   FAILED: {resp.status_code} {resp.text[:200]}")
        return

    print("\nContabo connection test passed.")


if __name__ == "__main__":
    asyncio.run(main())
