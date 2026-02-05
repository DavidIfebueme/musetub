from __future__ import annotations

import asyncio
import ssl
from email.message import EmailMessage
from email.utils import formataddr
import smtplib

from app.platform.config import settings


class EmailServiceError(RuntimeError):
    pass


def _require_smtp_settings() -> None:
    required = [
        settings.smtp_host,
        settings.smtp_username,
        settings.smtp_password,
        settings.smtp_from_email,
        settings.contact_recipient_email,
    ]
    if any(v is None or str(v).strip() == "" for v in required):
        raise EmailServiceError("SMTP settings are not fully configured")


def _build_message(*, subject: str, body: str, reply_to: str | None = None) -> EmailMessage:
    _require_smtp_settings()

    msg = EmailMessage()
    msg["Subject"] = subject
    from_name = settings.smtp_from_name or "MuseTub"
    msg["From"] = formataddr((from_name, settings.smtp_from_email or ""))
    msg["To"] = settings.contact_recipient_email
    if reply_to:
        msg["Reply-To"] = reply_to

    msg.set_content(body)
    return msg


def _send_message(msg: EmailMessage) -> None:
    _require_smtp_settings()

    host = settings.smtp_host or ""
    port = int(settings.smtp_port)
    username = settings.smtp_username or ""
    password = settings.smtp_password or ""

    if settings.smtp_use_ssl:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(host, port, context=context, timeout=10) as client:
            client.login(username, password)
            client.send_message(msg)
        return

    with smtplib.SMTP(host, port, timeout=10) as client:
        client.ehlo()
        client.starttls(context=ssl.create_default_context())
        client.login(username, password)
        client.send_message(msg)


async def send_contact_email(*, subject: str, body: str, reply_to: str | None = None) -> None:
    msg = _build_message(subject=subject, body=body, reply_to=reply_to)
    await asyncio.to_thread(_send_message, msg)
