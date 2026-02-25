#!/usr/bin/env python3
"""
One-off: set root_password for an instance by IP so Telegram auto-apply (SSH) can run.

Usage:
  cd backend
  export DATABASE_URL=postgresql+asyncpg://...
  python scripts/set_instance_root_password.py 109.199.102.120 'clawhost@123'

Then add your Telegram token on the Telegram Setup page and click Save & Connect;
the worker will SSH to this instance and apply the Telegram config.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Instance
from app.db.session import async_session_maker


async def set_password(ip_address: str, password: str) -> None:
    async with async_session_maker() as session:
        result = await session.execute(select(Instance).where(Instance.ip_address == ip_address))
        instance = result.scalar_one_or_none()
        if not instance:
            print(f"No instance found with ip_address={ip_address!r}", file=sys.stderr)
            sys.exit(1)
        instance.root_password = password
        session.add(instance)
        await session.commit()
        print(f"Updated instance id={instance.id} (ip={ip_address}): root_password set.")
        print("You can now add your Telegram token on the Telegram Setup page and click Save & Connect.")


def main() -> None:
    if not os.environ.get("DATABASE_URL"):
        print("Set DATABASE_URL (e.g. postgresql+asyncpg://user:pass@host:5432/db).", file=sys.stderr)
        sys.exit(1)
    if len(sys.argv) != 3:
        print("Usage: python scripts/set_instance_root_password.py <ip_address> <password>", file=sys.stderr)
        print("Example: python scripts/set_instance_root_password.py 109.199.102.120 'clawhost@123'", file=sys.stderr)
        sys.exit(1)
    ip_address = sys.argv[1].strip()
    password = sys.argv[2]
    asyncio.run(set_password(ip_address, password))


if __name__ == "__main__":
    main()
