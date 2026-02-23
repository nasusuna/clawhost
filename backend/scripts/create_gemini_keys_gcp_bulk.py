#!/usr/bin/env python3
"""
Create multiple Gemini API keys via Google Cloud API Keys API and store them in ClawHost DB (gemini_key_pool).

Same prerequisites as create_gemini_key_gcp.py:
  - GCP project with API Keys API and Generative Language API enabled
  - Service account with role "API Keys Admin"
  - GOOGLE_APPLICATION_CREDENTIALS or gcloud auth application-default login

Usage:
  cd backend
  pip install google-cloud-api-keys
  export GOOGLE_CLOUD_PROJECT=your-gcp-project-id   # or GCP_PROJECT_ID
  export DATABASE_URL=postgresql+asyncpg://...
  python scripts/create_gemini_keys_gcp_bulk.py [N]

  N = number of keys to create (default 5). Example: python scripts/create_gemini_keys_gcp_bulk.py 10
"""
import asyncio
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main() -> None:
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCP_PROJECT_ID")
    if not project_id:
        print("Set GOOGLE_CLOUD_PROJECT or GCP_PROJECT_ID.", file=sys.stderr)
        sys.exit(1)
    if not os.environ.get("DATABASE_URL"):
        print("Set DATABASE_URL (e.g. postgresql+asyncpg://user:pass@host:5432/db).", file=sys.stderr)
        sys.exit(1)

    try:
        n = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    except ValueError:
        print("Usage: create_gemini_keys_gcp_bulk.py [N]", file=sys.stderr)
        sys.exit(1)
    if n < 1 or n > 50:
        print("N must be between 1 and 50.", file=sys.stderr)
        sys.exit(1)

    from app.gemini_pool.gcp import create_one_key_via_gcp, store_key_in_pool

    print(f"Creating {n} Gemini API key(s) via GCP and storing in gemini_key_pool...")
    created = 0
    for i in range(n):
        try:
            key_string = create_one_key_via_gcp(project_id, display_name=f"ClawHost Gemini pool #{i+1}")
            asyncio.run(store_key_in_pool(key_string))
            created += 1
            print(f"  {created}/{n} created and stored.")
            if i < n - 1:
                time.sleep(2)  # avoid GCP rate limits
        except Exception as e:
            print(f"  Failed at key {created + 1}: {e}", file=sys.stderr)
            break
    print(f"Done. {created} key(s) in pool. Check: GET /admin/gemini-key-pool with X-Admin-Secret.")


if __name__ == "__main__":
    main()
