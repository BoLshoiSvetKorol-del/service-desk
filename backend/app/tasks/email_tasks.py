import asyncio
import logging
from app.tasks.celery_app import celery
from app.services.email_service import send_template_email

logger = logging.getLogger(__name__)


@celery.task(name="app.tasks.email_tasks.send_email_task", bind=True, max_retries=3, default_retry_delay=60)
def send_email_task(self, to: str | list[str], template: str, context: dict, subject: str = "") -> None:
    """Отправить email по шаблону. Вызывать через .delay()."""
    try:
        asyncio.run(send_template_email(to, subject, template, context))
    except Exception as exc:
        logger.error("Email task failed: %s", exc)
        raise self.retry(exc=exc)
