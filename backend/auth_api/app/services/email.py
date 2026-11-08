import asyncio
import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings
from app.core.errors import AuthUnavailableError

logger = logging.getLogger(__name__)


def ensure_email_configured() -> None:
    if not settings.SMTP_HOST:
        raise AuthUnavailableError("Email delivery is not configured")


async def send_action_email(email: str, token: str, purpose: str) -> None:
    ensure_email_configured()

    action = "verify your email" if purpose == "email_verification" else "reset your password"
    endpoint = "verify-email" if purpose == "email_verification" else "reset-password"
    url = f"{settings.FRONTEND_URL.rstrip('/')}/{endpoint}?token={token}"
    message = EmailMessage()
    message["Subject"] = f"LaunchPad: {action}"
    message["From"] = settings.SMTP_FROM_EMAIL
    message["To"] = email
    message.set_content(
        f"Use the following link to {action}:\n\n{url}\n\n"
        "If you did not request this, you can ignore this message."
    )

    try:
        await asyncio.to_thread(_send_message, message)
    except (OSError, smtplib.SMTPException):
        logger.exception("Could not deliver account email")
        raise AuthUnavailableError("Email delivery is temporarily unavailable")


def _send_message(message: EmailMessage) -> None:
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as smtp:
        if settings.SMTP_USE_TLS:
            smtp.starttls()
        if settings.SMTP_USERNAME:
            smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD or "")
        smtp.send_message(message)
