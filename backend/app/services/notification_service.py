import json
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.models.ticket import Ticket
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)

# Человекочитаемые описания событий
_EVENT_MESSAGES = {
    "ticket_created": "Заявка {number} создана",
    "ticket_status_changed": "Заявка {number}: статус изменён на «{new_status}»",
    "ticket_assigned": "Заявка {number} назначена на вас",
    "new_comment": "Новый комментарий к заявке {number}",
    "sla_warning": "Заявка {number}: SLA истекает менее чем через 1 час",
    "sla_violated": "Заявка {number}: SLA нарушен",
}


async def create_notification(
    db: AsyncSession,
    user_id: int,
    ticket_id: int | None,
    event_type: str,
    message: str,
) -> Notification:
    notif = Notification(
        user_id=user_id,
        ticket_id=ticket_id,
        event_type=event_type,
        message=message,
    )
    db.add(notif)
    await db.flush()
    return notif


async def publish_sse(redis, channel: str, event_type: str, data: dict) -> None:
    try:
        payload = json.dumps({"event": event_type, "data": data})
        await redis.publish(channel, payload)
    except Exception as exc:
        logger.warning("SSE publish to %s failed: %s", channel, exc)


async def notify_ticket_event(
    db: AsyncSession,
    redis,
    ticket: Ticket,
    event_type: str,
    actor: User,
    extra: dict | None = None,
) -> None:
    """Создать уведомления в БД + опубликовать SSE для всех получателей."""
    extra = extra or {}
    msg_template = _EVENT_MESSAGES.get(event_type, "Событие по заявке {number}")
    message = msg_template.format(number=ticket.number, **extra)

    sse_data = {"ticket_id": ticket.id, "ticket_number": ticket.number, **extra}

    # Определяем получателей
    recipients: set[int] = set()

    if event_type in ("ticket_status_changed", "new_comment"):
        # Заявитель (если не он сам инициатор)
        if ticket.requester_id != actor.id:
            recipients.add(ticket.requester_id)
        # Исполнитель
        if ticket.assignee_id and ticket.assignee_id != actor.id:
            recipients.add(ticket.assignee_id)

    elif event_type == "ticket_assigned":
        if ticket.assignee_id:
            recipients.add(ticket.assignee_id)

    elif event_type == "ticket_created":
        recipients.add(ticket.requester_id)

    # Создаём уведомления в БД и публикуем SSE каждому получателю
    for user_id in recipients:
        await create_notification(db, user_id, ticket.id, event_type, message)
        await publish_sse(redis, f"sse:user:{user_id}", event_type, sse_data)

    # Публикуем в канал отдела (для агентов дежурного отдела)
    if ticket.department_id:
        await publish_sse(redis, f"sse:department:{ticket.department_id}", event_type, sse_data)

    await db.commit()
