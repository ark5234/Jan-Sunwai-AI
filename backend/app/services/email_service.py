from __future__ import annotations

import asyncio
import logging
import smtplib
from email.message import EmailMessage
from pathlib import Path

from app.config import settings

_LOG_DIR = Path(__file__).resolve().parents[2] / "logs"
_LOG_DIR.mkdir(parents=True, exist_ok=True)
_LOG_FILE = _LOG_DIR / "email_stub.log"

_logger = logging.getLogger("JanSunwaiAI.EmailStub")
if not _logger.handlers:
    handler = logging.FileHandler(_LOG_FILE, encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    handler.setFormatter(formatter)
    _logger.addHandler(handler)
    _logger.setLevel(logging.INFO)


def _try_send_smtp(to_email: str, subject: str, body: str) -> bool:
    """
    P1-G: Send via SMTP with STARTTLS + optional authentication.
    Returns True on success, False if SMTP not configured.
    """
    if not settings.smtp_host:
        return False

    msg = EmailMessage()
    msg["From"] = settings.smtp_from
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
        smtp.ehlo()
        smtp.starttls()  # P1-G: upgrade to encrypted channel before any auth/data
        smtp.ehlo()      # re-identify after STARTTLS
        if settings.smtp_username and settings.smtp_password:
            smtp.login(settings.smtp_username, settings.smtp_password)
        smtp.send_message(msg)
    return True


def send_status_update_email(
    to_email: str,
    complaint_id: str,
    department: str,
    status_to: str,
    message: str,
) -> None:
    subject = f"[Jan-Sunwai] Complaint {complaint_id} status updated to {status_to}"
    body = (
        f"Complaint ID: {complaint_id}\n"
        f"Department: {department}\n"
        f"New Status: {status_to}\n\n"
        f"Message: {message}\n"
    )

    try:
        if _try_send_smtp(to_email, subject, body):
            _logger.info("SMTP_SENT status_update complaint=%s", complaint_id)
            return
    except Exception as exc:
        _logger.warning("SMTP_SEND_FAILED status_update complaint=%s err=%s", complaint_id, exc)

    # BL-03: Stub log — omit PII (email address, full subject, message body)
    _logger.info("STUB_EMAIL type=status_update complaint=%s status=%s", complaint_id, status_to)


def send_password_reset_email(to_email: str, reset_token: str) -> None:
    subject = "[Jan-Sunwai] Password Reset Request"
    body = (
        "A password reset was requested for your account.\n\n"
        f"Reset token: {reset_token}\n"
        "This token expires in 30 minutes.\n"
        "If you did not request this reset, ignore this message.\n"
    )

    try:
        if _try_send_smtp(to_email, subject, body):
            _logger.info("SMTP_SENT password_reset [recipient_omitted]")
            return
    except Exception as exc:
        _logger.warning("SMTP_SEND_FAILED password_reset err=%s", exc)

    # BL-03: Never log reset token or email — treat both as credentials
    _logger.info("STUB_EMAIL type=password_reset [recipient_and_token_omitted]")
