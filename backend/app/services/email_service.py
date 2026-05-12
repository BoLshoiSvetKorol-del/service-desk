import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import httpx
from jinja2 import Environment, FileSystemLoader, select_autoescape
from app.config import settings

logger = logging.getLogger(__name__)

_TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "templates"

_jinja_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    autoescape=select_autoescape(["html"]),
)


def render_template(template_name: str, context: dict) -> str:
    return _jinja_env.get_template(template_name).render(**context)


async def _send_via_sendgrid(recipients: list[str], subject: str, html_content: str) -> None:
    payload = {
        "personalizations": [{"to": [{"email": r} for r in recipients]}],
        "from": {"email": settings.MAIL_FROM, "name": settings.MAIL_FROM_NAME},
        "subject": subject,
        "content": [{"type": "text/html", "value": html_content}],
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={
                "Authorization": f"Bearer {settings.SENDGRID_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=10,
        )
    if response.status_code >= 400:
        logger.error("SendGrid error %d: %s", response.status_code, response.text)
    else:
        logger.info("Email sent via SendGrid to %s", recipients)


def _send_via_smtp(recipients: list[str], subject: str, html_content: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{settings.MAIL_FROM_NAME} <{settings.MAIL_FROM}>"
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    context = ssl.create_default_context() if settings.SMTP_TLS else None

    if settings.SMTP_TLS and settings.SMTP_PORT == 465:
        with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, context=context) as server:
            if settings.SMTP_USER:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.MAIL_FROM, recipients, msg.as_string())
    else:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_TLS:
                server.starttls(context=context)
            if settings.SMTP_USER:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.MAIL_FROM, recipients, msg.as_string())

    logger.info("Email sent via SMTP to %s", recipients)


async def send_email(to: str | list[str], subject: str, html_content: str) -> None:
    recipients = [to] if isinstance(to, str) else to

    if settings.SENDGRID_API_KEY and not settings.SENDGRID_API_KEY.startswith("SG.xxx"):
        await _send_via_sendgrid(recipients, subject, html_content)
    elif settings.SMTP_HOST:
        _send_via_smtp(recipients, subject, html_content)
    else:
        logger.warning("Email transport not configured — email to %s skipped", recipients)


async def send_template_email(to: str | list[str], subject: str, template_name: str, context: dict) -> None:
    html = render_template(template_name, context)
    await send_email(to, subject, html)
