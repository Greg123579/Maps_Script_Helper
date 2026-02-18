"""
Email utilities for password reset. Uses SMTP.
Configure SMTP_* in secrets.py or env vars.
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

def _get_config(name: str, default: str = ""):
    try:
        from backend import secrets
        return getattr(secrets, name, None) or os.getenv(name, default)
    except ImportError:
        return os.getenv(name, default)

SMTP_HOST = _get_config("SMTP_HOST", "")
SMTP_PORT = int(_get_config("SMTP_PORT", "587"))
SMTP_USER = _get_config("SMTP_USER", "")
SMTP_PASSWORD = _get_config("SMTP_PASSWORD", "")
SMTP_FROM = _get_config("SMTP_FROM", "")
APP_BASE_URL = _get_config("APP_BASE_URL", "")


def is_email_configured() -> bool:
    """Return True if SMTP is configured enough to send reset emails."""
    return bool(SMTP_HOST and SMTP_USER and SMTP_PASSWORD and SMTP_FROM and APP_BASE_URL)


def send_password_reset_email(to_email: str, reset_token: str) -> bool:
    """
    Send a password reset email. Returns True on success, False on failure.
    """
    if not is_email_configured():
        return False
    reset_url = f"{APP_BASE_URL.rstrip('/')}/?reset_token={reset_token}"
    subject = "Maps Script Helper - Reset your password"
    greeting = "Hi,"
    body_plain = f"""{greeting}

You requested a password reset for Maps Script Helper.

Click the link below to set a new password (link expires in 1 hour):

{reset_url}

If you didn't request this, you can ignore this email.

— Maps Script Helper
"""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SMTP_FROM
    msg["To"] = to_email
    msg.attach(MIMEText(body_plain, "plain", "utf-8"))
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_FROM, [to_email], msg.as_string())
        return True
    except Exception as e:
        print(f"[Email] Failed to send reset email: {e}")
        return False
