"""ARQ worker settings and enqueue helper."""
import uuid

from arq import create_pool
from arq.connections import RedisSettings

from app.config import settings
from app.queue.tasks import provision_instance


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


# Worker entrypoint: run with: arq app.queue.worker.WorkerSettings
class WorkerSettings:
    functions = [provision_instance]
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    max_jobs = 5
    job_timeout = 3600
