from celery import Celery
from celery.schedules import crontab
from app.config import settings

celery = Celery(
    "servicedesk",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.email_tasks",
        "app.tasks.sla_tasks",
    ],
)

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
)

celery.conf.beat_schedule = {
    "check-sla-warnings": {
        "task": "app.tasks.sla_tasks.check_sla_warnings",
        "schedule": 15 * 60,  # каждые 15 минут
    },
    "check-sla-violations": {
        "task": "app.tasks.sla_tasks.check_sla_violations",
        "schedule": 10 * 60,  # каждые 10 минут
    },
    "escalate-overdue": {
        "task": "app.tasks.sla_tasks.escalate_overdue",
        "schedule": 30 * 60,  # каждые 30 минут
    },
}
