"""Send transactional emails (Resend or stub)."""
from app.config import settings


async def send_provisioning_done(to_email: str, login_url: str, instance_domain: str, ip_address: str) -> None:
    if not settings.resend_api_key:
        return
    # TODO: Resend API send email with login_url, credentials, IP
    _ = to_email, login_url, instance_domain, ip_address


async def send_payment_failed(to_email: str) -> None:
    if not settings.resend_api_key:
        return
    # TODO: Resend API
    _ = to_email


async def send_subscription_canceled(to_email: str) -> None:
    if not settings.resend_api_key:
        return
    # TODO: Resend API
    _ = to_email
