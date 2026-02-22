#!/usr/bin/env python3
"""
Create one Gemini API key via Google Cloud API Keys API and store it in the ClawHost DB (gemini_key_pool).

Prerequisites:
  - GCP project with API Keys API and Generative Language API enabled
  - Service account with role "API Keys Admin" (or apikeys.keys.create)
  - Application Default Credentials: set GOOGLE_APPLICATION_CREDENTIALS to the service account JSON path,
    or run with: gcloud auth application-default login

Usage:
  cd backend
  pip install google-cloud-api-keys  # if not already in requirements
  export GOOGLE_CLOUD_PROJECT=your-gcp-project-id   # or GCP_PROJECT_ID
  export DATABASE_URL=postgresql+asyncpg://...
  python scripts/create_gemini_key_gcp.py

Optional:
  GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

Automation: set GEMINI_KEY_POOL_REPLENISH_ENABLED=true and GCP_PROJECT_ID (or GOOGLE_CLOUD_PROJECT)
in backend env; the ARQ worker cron will replenish the pool every 6 hours. See docs/PRODUCTION.md.
"""
import asyncio
import os
import sys

# Add backend to path so app imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main() -> None:
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCP_PROJECT_ID")
    if not project_id:
        print("Set GOOGLE_CLOUD_PROJECT or GCP_PROJECT_ID to your GCP project ID.", file=sys.stderr)
        sys.exit(1)
    if not os.environ.get("DATABASE_URL"):
        print("Set DATABASE_URL (e.g. postgresql+asyncpg://user:pass@host:5432/db).", file=sys.stderr)
        sys.exit(1)

    from app.gemini_pool.gcp import create_one_key_via_gcp, store_key_in_pool

    print("Creating API key via GCP API Keys API (restricted to generativelanguage.googleapis.com)...")
    key_string = create_one_key_via_gcp(project_id)
    print("Key created.")
    asyncio.run(store_key_in_pool(key_string))
    print("Stored in gemini_key_pool. Check pool: GET /admin/gemini-key-pool with X-Admin-Secret.")


if __name__ == "__main__":
    main()
