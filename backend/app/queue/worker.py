"""ARQ worker settings and enqueue helper."""
import uuid

from arq import create_pool
from arq.connections import RedisSettings
from arq.cron import cron

from app.config import settings
from app.queue.tasks import provision_instance, replenish_gemini_key_pool


async def enqueue_provision_job(user_id: uuid.UUID, subscription_id: uuid.UUID, plan_type: str) -> str:
    """Enqueue provisioning job; return ARQ job_id."""
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    pool = await create_pool(redis_settings)
    job = await pool.enqueue_job(
        "provision_instance",
        str(user_id),
        str(subscription_id),
        plan_type,
    )
    await pool.close()
    return job.job_id if job else ""


# Cron: replenish Gemini key pool every 6 hours when enabled (GEMINI_KEY_POOL_REPLENISH_ENABLED).
_replenish_cron = cron(
    replenish_gemini_key_pool,
    hour={0, 6, 12, 18},
    minute=0,
    run_at_startup=False,
    unique=True,
    timeout=600,
)

# Worker entrypoint: run with: arq app.queue.worker.WorkerSettings
class WorkerSettings:
    functions = [provision_instance, replenish_gemini_key_pool]
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    max_jobs = 5
    job_timeout = 3600
    cron_jobs = [_replenish_cron]
