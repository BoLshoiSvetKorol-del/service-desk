from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, func
from fastapi import HTTPException, status

from app.models.ticket import Ticket, TicketStatus
from app.models.ticket_history import TicketHistory
from app.models.user import User, UserRole
from app.models.priority import Priority, PriorityLevel
from app.models.ticket_type import TicketType
from app.models.department import Department
from app.utils.ticket_number import generate_ticket_number

# Матрица допустимых переходов: (from, to) → set of allowed roles
ALLOWED_TRANSITIONS: dict[tuple[TicketStatus, TicketStatus], set[UserRole]] = {
    (TicketStatus.new, TicketStatus.in_progress): {UserRole.agent, UserRole.admin},
    (TicketStatus.new, TicketStatus.cancelled): {UserRole.admin, UserRole.user, UserRole.agent},
    (TicketStatus.in_progress, TicketStatus.waiting_info): {UserRole.agent, UserRole.admin},
    (TicketStatus.in_progress, TicketStatus.resolved): {UserRole.agent, UserRole.admin},
    (TicketStatus.in_progress, TicketStatus.cancelled): {UserRole.agent, UserRole.admin},
    (TicketStatus.waiting_info, TicketStatus.in_progress): {UserRole.user, UserRole.agent, UserRole.admin},
    (TicketStatus.waiting_info, TicketStatus.cancelled): {UserRole.agent, UserRole.admin},
    (TicketStatus.resolved, TicketStatus.in_progress): {UserRole.user, UserRole.admin},
}

TERMINAL_STATUSES = {TicketStatus.resolved, TicketStatus.cancelled}


def _check_ticket_access(ticket: Ticket, user: User) -> None:
    if user.role == UserRole.admin:
        return
    if user.role == UserRole.agent:
        if (ticket.department_id == user.department_id
                or ticket.assignee_id == user.id
                or ticket.requester_id == user.id):
            return
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к заявке")
    if ticket.requester_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к заявке")


async def create_ticket(db: AsyncSession, data, user: User) -> Ticket:
    if data.priority_id is not None:
        priority = await db.get(Priority, data.priority_id)
        if not priority:
            raise HTTPException(status_code=404, detail="Приоритет не найден")
    else:
        priority = await db.scalar(select(Priority).where(Priority.level == PriorityLevel.normal))
        if not priority:
            priority = await db.scalar(select(Priority).order_by(Priority.id))
        if not priority:
            raise HTTPException(status_code=404, detail="Приоритеты не настроены")

    ticket_type = await db.get(TicketType, data.type_id)
    if not ticket_type:
        raise HTTPException(status_code=404, detail="Тип заявки не найден")
    if not ticket_type.is_active:
        raise HTTPException(status_code=400, detail="Тип заявки неактивен")

    department_id = data.department_id or ticket_type.default_department_id

    number = await generate_ticket_number(db)

    from app.services.sla_service import calculate_deadline
    sla_deadline = calculate_deadline(datetime.now(timezone.utc), priority.sla_hours)

    ticket = Ticket(
        number=number,
        title=data.title,
        description=data.description,
        status=TicketStatus.new,
        priority_id=data.priority_id,
        type_id=data.type_id,
        requester_id=user.id,
        department_id=department_id,
        sla_deadline=sla_deadline,
        sla_extra_minutes=0,
        sla_violated=False,
    )
    db.add(ticket)
    await db.flush()

    history = TicketHistory(
        ticket_id=ticket.id,
        user_id=user.id,
        event_type="created",
        payload={"title": ticket.title, "priority_id": ticket.priority_id, "type_id": ticket.type_id},
    )
    db.add(history)
    await db.commit()
    await db.refresh(ticket)

    # Email создателю
    try:
        from app.tasks.email_tasks import send_email_task
        send_email_task.delay(
            to=user.email,
            template="ticket_created.html",
            context={
                "requester_name": user.full_name,
                "ticket_number": ticket.number,
                "ticket_title": ticket.title,
                "priority": priority.name,
                "sla_deadline": sla_deadline.strftime("%d.%m.%Y %H:%M UTC"),
            },
            subject=f"Заявка {ticket.number} зарегистрирована",
        )
    except Exception:
        pass

    return ticket


async def change_status(
    db: AsyncSession, ticket: Ticket, new_status: TicketStatus, user: User, comment: str | None = None
) -> Ticket:
    old_status = ticket.status
    transition = (old_status, new_status)

    if transition not in ALLOWED_TRANSITIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Переход {old_status.value} → {new_status.value} не разрешён",
        )

    allowed_roles = ALLOWED_TRANSITIONS[transition]
    if user.role not in allowed_roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав для этого перехода")

    # Requester может отменить только свою заявку
    if user.role == UserRole.user and new_status == TicketStatus.cancelled:
        if ticket.requester_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к заявке")

    # Requester может переоткрыть только если прошло ≤ 72 часов
    if user.role == UserRole.user and new_status == TicketStatus.in_progress and old_status == TicketStatus.resolved:
        from app.services.sla_service import REOPEN_WINDOW_HOURS
        if ticket.closed_at:
            elapsed = (datetime.now(timezone.utc) - ticket.closed_at).total_seconds() / 3600
            if elapsed > REOPEN_WINDOW_HOURS:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Окно переоткрытия истекло (72 ч)")

    from app.services.sla_service import pause_sla, resume_sla

    if new_status == TicketStatus.waiting_info:
        pause_sla(ticket)
    elif old_status == TicketStatus.waiting_info and new_status == TicketStatus.in_progress:
        resume_sla(ticket)

    if new_status in TERMINAL_STATUSES:
        ticket.closed_at = datetime.now(timezone.utc)
    elif new_status == TicketStatus.in_progress and old_status == TicketStatus.resolved:
        ticket.closed_at = None

    ticket.status = new_status

    history = TicketHistory(
        ticket_id=ticket.id,
        user_id=user.id,
        event_type="status_changed",
        payload={"old_status": old_status.value, "new_status": new_status.value, "comment": comment},
    )
    db.add(history)
    await db.commit()
    await db.refresh(ticket)

    # Email заявителю об изменении статуса
    try:
        from app.tasks.email_tasks import send_email_task
        from app.models.user import User as _User
        requester = await db.get(_User, ticket.requester_id)
        if requester:
            send_email_task.delay(
                to=requester.email,
                template="ticket_status_changed.html",
                context={
                    "recipient_name": requester.full_name,
                    "ticket_number": ticket.number,
                    "ticket_title": ticket.title,
                    "old_status": old_status.value,
                    "new_status": new_status.value,
                    "actor_name": user.full_name,
                    "comment": comment,
                },
                subject=f"Заявка {ticket.number}: статус изменён",
            )
    except Exception:
        pass

    return ticket


async def assign_ticket(
    db: AsyncSession, ticket: Ticket, user: User, assignee_id: int | None, department_id: int | None
) -> Ticket:
    old_assignee = ticket.assignee_id
    old_dept = ticket.department_id
    new_assignee_name: str | None = None
    new_department_name: str | None = None

    if assignee_id is not None:
        assignee = await db.get(User, assignee_id)
        if not assignee:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        if assignee.role == UserRole.user:
            raise HTTPException(status_code=400, detail="Нельзя назначить роль 'user' исполнителем")
        ticket.assignee_id = assignee_id
        new_assignee_name = assignee.full_name or assignee.username
    else:
        ticket.assignee_id = None

    if department_id is not None:
        dept = await db.get(Department, department_id)
        if not dept:
            raise HTTPException(status_code=404, detail="Отдел не найден")
        ticket.department_id = department_id
        new_department_name = dept.name

    history = TicketHistory(
        ticket_id=ticket.id,
        user_id=user.id,
        event_type="assigned",
        payload={
            "old_assignee_id": old_assignee,
            "new_assignee_id": ticket.assignee_id,
            "new_assignee_name": new_assignee_name,
            "old_department_id": old_dept,
            "new_department_id": ticket.department_id,
            "new_department_name": new_department_name,
        },
    )
    db.add(history)
    await db.commit()
    await db.refresh(ticket)

    # Email новому исполнителю
    if assignee_id and assignee_id != old_assignee:
        try:
            from app.tasks.email_tasks import send_email_task
            from app.models.user import User as _User
            from app.models.priority import Priority as _Priority
            assignee = await db.get(_User, assignee_id)
            requester = await db.get(_User, ticket.requester_id)
            priority = await db.get(_Priority, ticket.priority_id)
            if assignee:
                send_email_task.delay(
                    to=assignee.email,
                    template="ticket_assigned.html",
                    context={
                        "assignee_name": assignee.full_name,
                        "ticket_number": ticket.number,
                        "ticket_title": ticket.title,
                        "requester_name": requester.full_name if requester else "—",
                        "priority": priority.name if priority else "—",
                        "sla_deadline": ticket.sla_deadline.strftime("%d.%m.%Y %H:%M UTC") if ticket.sla_deadline else "—",
                    },
                    subject=f"Заявка {ticket.number} назначена на вас",
                )
        except Exception:
            pass

    return ticket


async def merge_ticket(
    db: AsyncSession, source: Ticket, target_id: int, user: User, comment: str | None = None
) -> Ticket:
    if source.id == target_id:
        raise HTTPException(status_code=400, detail="Нельзя объединить заявку с самой собой")

    target = await db.get(Ticket, target_id)
    if not target:
        raise HTTPException(status_code=404, detail="Целевая заявка не найдена")

    if source.status in (TicketStatus.merged, TicketStatus.resolved, TicketStatus.cancelled):
        raise HTTPException(status_code=422, detail=f"Нельзя объединить заявку со статусом {source.status.value}")

    if target.status == TicketStatus.merged:
        raise HTTPException(status_code=422, detail="Целевая заявка уже объединена с другой")

    source.status = TicketStatus.merged
    source.merged_into_id = target_id
    source.closed_at = datetime.now(timezone.utc)

    history = TicketHistory(
        ticket_id=source.id,
        user_id=user.id,
        event_type="merged",
        payload={"merged_into_id": target_id, "target_number": target.number, "comment": comment},
    )
    db.add(history)
    await db.commit()
    await db.refresh(source)
    return source


async def get_tickets(db: AsyncSession, user: User, filters: dict) -> tuple[list[Ticket], int]:
    query = select(Ticket)

    # Фильтр по роли
    if user.role == UserRole.user:
        query = query.where(Ticket.requester_id == user.id)
    elif user.role == UserRole.agent:
        query = query.where(
            or_(
                Ticket.department_id == user.department_id,
                Ticket.assignee_id == user.id,
                Ticket.requester_id == user.id,
            )
        )

    # Прикладные фильтры
    if filters.get("status"):
        statuses = [TicketStatus(s) for s in filters["status"].split(",") if s]
        query = query.where(Ticket.status.in_(statuses))

    if filters.get("priority_id"):
        ids = [int(i) for i in str(filters["priority_id"]).split(",") if i]
        query = query.where(Ticket.priority_id.in_(ids))

    if filters.get("type_id"):
        query = query.where(Ticket.type_id == filters["type_id"])

    if filters.get("department_id"):
        query = query.where(Ticket.department_id == filters["department_id"])

    if filters.get("assignee_id"):
        query = query.where(Ticket.assignee_id == filters["assignee_id"])

    if filters.get("requester_id"):
        query = query.where(Ticket.requester_id == filters["requester_id"])

    if filters.get("sla_violated") is not None:
        query = query.where(Ticket.sla_violated == filters["sla_violated"])

    if filters.get("search"):
        pattern = f"%{filters['search']}%"
        query = query.where(
            or_(Ticket.number.ilike(pattern), Ticket.title.ilike(pattern))
        )

    if filters.get("date_from"):
        query = query.where(Ticket.created_at >= filters["date_from"])

    if filters.get("date_to"):
        query = query.where(Ticket.created_at <= filters["date_to"])

    total = await db.scalar(select(func.count()).select_from(query.subquery()))

    sort_col = getattr(Ticket, filters.get("sort_by", "created_at"), Ticket.created_at)
    if filters.get("sort_order", "desc") == "asc":
        query = query.order_by(sort_col.asc())
    else:
        query = query.order_by(sort_col.desc())

    page = filters.get("page", 1)
    page_size = filters.get("page_size", 20)
    result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))
    return result.scalars().all(), total or 0
