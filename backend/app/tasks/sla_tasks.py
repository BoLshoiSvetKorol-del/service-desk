import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta

from app.tasks.celery_app import celery

logger = logging.getLogger(__name__)

_WARNING_THRESHOLD = timedelta(hours=1)
_ESCALATION_THRESHOLD = timedelta(hours=2)


def _run(coro):
    return asyncio.run(coro)


async def _get_session():
    from app.database import AsyncSessionLocal
    return AsyncSessionLocal()


async def _publish_sse(channel: str, event_type: str, data: dict) -> None:
    """Опубликовать событие в Redis-канал для SSE (Миссия 10)."""
    try:
        import redis.asyncio as aioredis
        from app.config import settings
        r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        payload = json.dumps({"event": event_type, "data": data})
        await r.publish(channel, payload)
        await r.aclose()
    except Exception as exc:
        logger.warning("SSE publish failed: %s", exc)


async def _do_check_sla_warnings() -> None:
    from sqlalchemy import select, and_
    from app.models.ticket import Ticket, TicketStatus
    from app.tasks.email_tasks import send_email_task

    now = datetime.now(timezone.utc)
    deadline_upper = now + _WARNING_THRESHOLD

    async with await _get_session() as db:
        result = await db.execute(
            select(Ticket).where(
                and_(
                    Ticket.sla_deadline > now,
                    Ticket.sla_deadline <= deadline_upper,
                    Ticket.status.not_in([TicketStatus.resolved, TicketStatus.cancelled]),
                    Ticket.sla_paused_at.is_(None),
                    Ticket.sla_violated.is_(False),
                )
            )
        )
        tickets = result.scalars().all()

    for ticket in tickets:
        logger.info("SLA warning: ticket %s deadline %s", ticket.number, ticket.sla_deadline)

        # Email исполнителю
        if ticket.assignee_id:
            async with await _get_session() as db:
                from app.models.user import User
                assignee = await db.get(User, ticket.assignee_id)
            if assignee and assignee.email:
                send_email_task.delay(
                    to=assignee.email,
                    template="sla_warning.html",
                    context={
                        "ticket_number": ticket.number,
                        "ticket_title": ticket.title,
                        "sla_deadline": ticket.sla_deadline.strftime("%d.%m.%Y %H:%M"),
                        "assignee_name": assignee.full_name,
                    },
                    subject=f"[SLA] Предупреждение по заявке {ticket.number}",
                )

        # SSE в канал отдела
        if ticket.department_id:
            await _publish_sse(
                f"sse:department:{ticket.department_id}",
                "sla_warning",
                {"ticket_id": ticket.id, "ticket_number": ticket.number},
            )


async def _do_check_sla_violations() -> None:
    from sqlalchemy import select, and_
    from app.models.ticket import Ticket, TicketStatus
    from app.tasks.email_tasks import send_email_task

    now = datetime.now(timezone.utc)

    async with await _get_session() as db:
        result = await db.execute(
            select(Ticket).where(
                and_(
                    Ticket.sla_deadline < now,
                    Ticket.status.not_in([TicketStatus.resolved, TicketStatus.cancelled]),
                    Ticket.sla_paused_at.is_(None),
                    Ticket.sla_violated.is_(False),
                )
            )
        )
        tickets = result.scalars().all()

        for ticket in tickets:
            ticket.sla_violated = True
            logger.info("SLA violated: ticket %s", ticket.number)

        await db.commit()

    for ticket in tickets:
        # SSE в канал отдела и исполнителя
        if ticket.department_id:
            await _publish_sse(
                f"sse:department:{ticket.department_id}",
                "sla_violated",
                {"ticket_id": ticket.id, "ticket_number": ticket.number},
            )
        if ticket.assignee_id:
            await _publish_sse(
                f"sse:user:{ticket.assignee_id}",
                "sla_violated",
                {"ticket_id": ticket.id, "ticket_number": ticket.number},
            )


async def _do_escalate_overdue() -> None:
    from sqlalchemy import select, and_
    from app.models.ticket import Ticket, TicketStatus
    from app.models.user import User, UserRole
    from app.tasks.email_tasks import send_email_task

    now = datetime.now(timezone.utc)
    overdue_since = now - _ESCALATION_THRESHOLD

    async with await _get_session() as db:
        result = await db.execute(
            select(Ticket).where(
                and_(
                    Ticket.sla_violated.is_(True),
                    Ticket.sla_deadline < overdue_since,
                    Ticket.status.not_in([TicketStatus.resolved, TicketStatus.cancelled]),
                )
            )
        )
        tickets = result.scalars().all()

    for ticket in tickets:
        if not ticket.department_id:
            continue

        async with await _get_session() as db:
            # Руководитель отдела — первый admin или agent отдела
            result = await db.execute(
                select(User).where(
                    and_(
                        User.department_id == ticket.department_id,
                        User.role == UserRole.agent,
                        User.is_active.is_(True),
                    )
                ).limit(1)
            )
            lead = result.scalar_one_or_none()

        if lead and lead.email:
            send_email_task.delay(
                to=lead.email,
                template="sla_violated.html",
                context={
                    "ticket_number": ticket.number,
                    "ticket_title": ticket.title,
                    "sla_deadline": ticket.sla_deadline.strftime("%d.%m.%Y %H:%M"),
                    "overdue_hours": round((now - ticket.sla_deadline).total_seconds() / 3600, 1),
                    "lead_name": lead.full_name,
                },
                subject=f"[ЭСКАЛАЦИЯ] Заявка {ticket.number} просрочена",
            )
            logger.info("Escalation sent for ticket %s to %s", ticket.number, lead.email)


@celery.task(name="app.tasks.sla_tasks.check_sla_warnings")
def check_sla_warnings() -> None:
    """Найти заявки с дедлайном < 1 часа — предупредить исполнителя."""
    _run(_do_check_sla_warnings())


@celery.task(name="app.tasks.sla_tasks.check_sla_violations")
def check_sla_violations() -> None:
    """Найти просроченные заявки, установить sla_violated=True."""
    _run(_do_check_sla_violations())


@celery.task(name="app.tasks.sla_tasks.escalate_overdue")
def escalate_overdue() -> None:
    """Эскалация: заявки просрочены >2ч — уведомить руководителя отдела."""
    _run(_do_escalate_overdue())
