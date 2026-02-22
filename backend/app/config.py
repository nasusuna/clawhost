"""Application configuration from environment."""
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR
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

    # Optional: Gemini API key used for new instances when user has not set one (shared key; you pay usage)
    gemini_api_key: str = ""

    # Admin: secret for key-pool and other admin endpoints (Header: X-Admin-Secret). If empty, admin routes return 403.
    admin_secret: str = ""

    # GCP: for automated Gemini key pool replenishment (create keys via API Keys API and store in DB).
    # Set GCP_PROJECT_ID or GOOGLE_CLOUD_PROJECT env; credentials via GOOGLE_APPLICATION_CREDENTIALS.
    gcp_project_id: str = ""  # env: GCP_PROJECT_ID or GOOGLE_CLOUD_PROJECT
    # Minimum number of unassigned keys to maintain; replenish cron creates keys when below this.
    gemini_key_pool_min_available: int = 2
    # Enable periodic replenish (ARQ cron). Requires gcp_project_id and ADC.
    gemini_key_pool_replenish_enabled: bool = False

    @model_validator(mode="after")
    def validate_production(self) -> "Settings":
        if self.app_env.lower() != "production":
            return self
        if not self.secret_key or self.secret_key == "change-me-in-production-min-32-chars" or len(self.secret_key) < 32:
            raise ValueError(
                "In production set SECRET_KEY to a strong value (min 32 chars). "
                "Generate with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
            )
        if not (self.cors_allowed_origins or "").strip():
            raise ValueError(
                "In production set CORS_ALLOWED_ORIGINS to your frontend URL(s), e.g. https://app.clawhost.com"
            )
        return self


settings = Settings()
