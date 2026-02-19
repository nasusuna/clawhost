"""Application configuration from environment."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    secret_key: str = "change-me-in-production-min-32-chars"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    # Comma-separated origins for CORS (e.g. https://app.clawhost.com,https://clawhost.com)
    cors_allowed_origins: str = ""

    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/clawhost"

    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_starter_price_id: str = ""
    stripe_pro_price_id: str = ""

    redis_url: str = "redis://localhost:6379/0"

    # Contabo: OAuth2 (client id/secret + API user/password from control panel)
    contabo_api_url: str = "https://api.contabo.com"
    contabo_client_id: str = ""
    contabo_client_secret: str = ""
    contabo_api_user: str = ""  # API user email
    contabo_api_password: str = ""

    cloudflare_api_token: str = ""
    cloudflare_zone_id: str = ""
    clawhost_base_domain: str = "customers.yourdomain.com"

    resend_api_key: str = ""
    email_from: str = "noreply@yourdomain.com"

    # OpenClaw on provisioned VPS (Docker image + port for Nginx proxy)
    openclaw_docker_image: str = "fourplayers/openclaw:latest"
    openclaw_app_port: int = 18789


settings = Settings()
