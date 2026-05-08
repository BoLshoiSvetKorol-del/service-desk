import logging
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


async def send_email(to: str | list[str], subject: str, html_content: str) -> None:
    if not settings.SENDGRID_API_KEY:
        logger.warning("SENDGRID_API_KEY not set — email to %s skipped", to)
        return

    recipients = [to] if isinstance(to, str) else to
    payload = {
        "personalizations": [{"to": [{"email": r} for r in recipients]}],
        "from": {"email": settings.MAIL_FROM},
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
        logger.info("Email sent to %s (subject: %s)", recipients, subject)


async def send_template_email(to: str | list[str], subject: str, template_name: str, context: dict) -> None:
    html = render_template(template_name, context)
    await send_email(to, subject, html)
