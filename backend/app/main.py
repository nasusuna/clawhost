"""ClawHost API — FastAPI app."""
import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.admin.routes import router as admin_router
from app.auth.routes import router as auth_router
from app.config import settings
from app.db.session import engine
from app.instances.routes import router as instances_router
from app.subscription.routes import router as subscription_router
from app.webhooks.routes import router as webhooks_router

# Logging: level from config, no sensitive data in format
_log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
logging.basicConfig(
    level=_log_level,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("ClawHost API starting (env=%s)", settings.app_env)
    yield
    logger.info("ClawHost API shutting down")


app = FastAPI(
    title="ClawHost API",
    description="Managed OpenClaw Hosting — subscriptions, provisioning, instances",
    version="0.1.0",
    lifespan=lifespan,
)

def _cors_origins() -> list[str]:
    if settings.cors_allowed_origins:
        return [o.strip() for o in settings.cors_allowed_origins.split(",") if o.strip()]
    return [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ]


_cors_kw: dict = {
    "allow_origins": _cors_origins(),
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
    "expose_headers": ["*"],
}
if not settings.cors_allowed_origins:
    _cors_kw["allow_origin_regex"] = r"^http://(localhost|127\.0\.0\.1)(:\d+)?$"
app.add_middleware(CORSMiddleware, **_cors_kw)

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(subscription_router)
app.include_router(instances_router)
app.include_router(webhooks_router)


@app.get("/health")
async def health() -> dict:
    """Liveness: always ok if the process is up."""
    return {"status": "ok"}


@app.get("/health/ready")
async def health_ready() -> dict:
    """Readiness: DB (and optionally Redis) reachable. Use for load balancers / k8s."""
    checks: dict[str, str] = {}
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        logger.warning("Readiness DB check failed: %s", e)
        checks["database"] = "error"

    try:
        from redis.asyncio import from_url
        r = from_url(settings.redis_url)
        await r.ping()
        await r.aclose()
        checks["redis"] = "ok"
    except Exception as e:
        logger.warning("Readiness Redis check failed: %s", e)
        checks["redis"] = "error"

    if any(v == "error" for v in checks.values()):
        return JSONResponse(status_code=503, content={"status": "degraded", "checks": checks})
    return {"status": "ready", "checks": checks}
