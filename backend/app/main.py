"""ClawHost API — FastAPI app."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.routes import router as auth_router
from app.config import settings
from app.instances.routes import router as instances_router
from app.subscription.routes import router as subscription_router
from app.webhooks.routes import router as webhooks_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # Shutdown: close Redis pool if any


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
app.include_router(subscription_router)
app.include_router(instances_router)
app.include_router(webhooks_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
