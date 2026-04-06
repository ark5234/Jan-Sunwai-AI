from __future__ import annotations

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
    if not settings.smtp_host:
        return False

    msg = EmailMessage()
    msg["From"] = settings.smtp_from
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
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
            _logger.info("SMTP_SENT status_update to=%s complaint=%s", to_email, complaint_id)
            return
    except Exception as exc:
        _logger.warning("SMTP_SEND_FAILED status_update to=%s complaint=%s err=%s", to_email, complaint_id, exc)

    _logger.info("STUB_EMAIL status_update to=%s subject=%s body=%s", to_email, subject, body)


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
            _logger.info("SMTP_SENT password_reset to=%s", to_email)
            return
    except Exception as exc:
        _logger.warning("SMTP_SEND_FAILED password_reset to=%s err=%s", to_email, exc)

    _logger.info("STUB_EMAIL password_reset to=%s subject=%s body=%s", to_email, subject, body)
