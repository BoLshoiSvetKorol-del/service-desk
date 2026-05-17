from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
import redis.asyncio as aioredis

from app.database import get_db
from app.models.ticket import Ticket, TicketStatus
from app.models.ticket_history import TicketHistory
from app.models.user import User, UserRole
from app.schemas.ticket import (
    TicketCreate, TicketUpdate, TicketResponse, TicketListItem,
    StatusChangeRequest, AssignRequest, PriorityChangeRequest, TicketHistoryResponse,
    MergeRequest,
)
from app.services.ticket_service import (
    create_ticket, change_status, assign_ticket, get_tickets, merge_ticket, _check_ticket_access,
)
from app.services.notification_service import notify_ticket_event
from app.redis import get_redis
from app.utils.pagination import PagedResponse
from app.utils.permissions import get_current_user, require_role

router = APIRouter()


@router.get("", response_model=PagedResponse[TicketListItem])
async def list_tickets(
    status_filter: str | None = Query(default=None, alias="status"),
    priority_id: str | None = Query(default=None),
    type_id: int | None = Query(default=None),
    department_id: int | None = Query(default=None),
    assignee_id: int | None = Query(default=None),
    requester_id: int | None = Query(default=None),
    sla_violated: bool | None = Query(default=None),
    search: str | None = Query(default=None, max_length=200),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    sort_by: str = Query(default="created_at"),
    sort_order: str = Query(default="desc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    filters = {
        "status": status_filter,
        "priority_id": priority_id,
        "type_id": type_id,
        "department_id": department_id,
        "assignee_id": assignee_id,
        "requester_id": requester_id,
        "sla_violated": sla_violated,
        "search": search,
        "date_from": date_from,
        "date_to": date_to,
        "sort_by": sort_by,
        "sort_order": sort_order,
        "page": page,
        "page_size": page_size,
    }
    tickets, total = await get_tickets(db, current_user, filters)
    return PagedResponse.build(
        items=[TicketListItem.model_validate(t) for t in tickets],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket_endpoint(
    data: TicketCreate,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    current_user: User = Depends(get_current_user),
):
    ticket = await create_ticket(db, data, current_user)
    await notify_ticket_event(db, redis, ticket, "ticket_created", current_user)
    return TicketResponse.model_validate(ticket)


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = await db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    _check_ticket_access(ticket, current_user)
    return TicketResponse.model_validate(ticket)


@router.put("/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: int,
    data: TicketUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.department_head, UserRole.agent)),
):
    ticket = await db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    _check_ticket_access(ticket, current_user)

    if data.title is not None:
        ticket.title = data.title
    if data.description is not None:
        ticket.description = data.description

    from app.models.ticket_history import TicketHistory
    db.add(TicketHistory(
        ticket_id=ticket.id,
        user_id=current_user.id,
        event_type="updated",
        payload={"title": data.title, "description": data.description},
    ))
    await db.commit()
    await db.refresh(ticket)
    return TicketResponse.model_validate(ticket)


@router.patch("/{ticket_id}/status", response_model=TicketResponse)
async def change_ticket_status(
    ticket_id: int,
    data: StatusChangeRequest,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    current_user: User = Depends(get_current_user),
):
    ticket = await db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    _check_ticket_access(ticket, current_user)
    updated = await change_status(db, ticket, data.status, current_user, data.comment)
    await notify_ticket_event(db, redis, updated, "ticket_status_changed", current_user,
                              {"new_status": data.status.value})
    return TicketResponse.model_validate(updated)


@router.patch("/{ticket_id}/assign", response_model=TicketResponse)
async def assign_ticket_endpoint(
    ticket_id: int,
    data: AssignRequest,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.department_head)),
):
    ticket = await db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    _check_ticket_access(ticket, current_user)
    updated = await assign_ticket(db, ticket, current_user, data.assignee_id, data.department_id)
    if data.assignee_id:
        await notify_ticket_event(db, redis, updated, "ticket_assigned", current_user)
    return TicketResponse.model_validate(updated)


@router.patch("/{ticket_id}/priority", response_model=TicketResponse)
async def change_ticket_priority(
    ticket_id: int,
    data: PriorityChangeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.department_head, UserRole.agent)),
):
    from app.models.priority import Priority
    ticket = await db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    _check_ticket_access(ticket, current_user)

    priority = await db.get(Priority, data.priority_id)
    if not priority:
        raise HTTPException(status_code=404, detail="Приоритет не найден")

    old_priority = await db.get(Priority, ticket.priority_id)
    ticket.priority_id = data.priority_id

    from app.models.ticket_history import TicketHistory
    db.add(TicketHistory(
        ticket_id=ticket.id,
        user_id=current_user.id,
        event_type="priority_changed",
        payload={
            "old_priority_id": old_priority.id if old_priority else None,
            "new_priority_id": data.priority_id,
            "old_priority_name": old_priority.level.value if old_priority else None,
            "new_priority_name": priority.level.value,
        },
    ))
    await db.commit()
    await db.refresh(ticket)
    return TicketResponse.model_validate(ticket)


@router.get("/{ticket_id}/history", response_model=list[TicketHistoryResponse])
async def get_ticket_history(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = await db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    _check_ticket_access(ticket, current_user)

    result = await db.execute(
        select(TicketHistory)
        .where(TicketHistory.ticket_id == ticket_id)
        .order_by(TicketHistory.created_at)
    )
    return [TicketHistoryResponse.model_validate(h) for h in result.scalars().all()]


@router.post("/{ticket_id}/merge", response_model=TicketResponse)
async def merge_ticket_endpoint(
    ticket_id: int,
    data: MergeRequest,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.department_head, UserRole.agent)),
):
    ticket = await db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    _check_ticket_access(ticket, current_user)
    updated = await merge_ticket(db, ticket, data.target_id, current_user, data.comment)
    await notify_ticket_event(db, redis, updated, "ticket_merged", current_user,
                              {"merged_into_id": data.target_id})
    return TicketResponse.model_validate(updated)


@router.get("/{ticket_id}/merged", response_model=list[TicketListItem])
async def get_merged_tickets(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = await db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    _check_ticket_access(ticket, current_user)
    result = await db.execute(
        select(Ticket).where(Ticket.merged_into_id == ticket_id).order_by(Ticket.created_at)
    )
    return [TicketListItem.model_validate(t) for t in result.scalars().all()]


@router.get("/{ticket_id}/duplicates", response_model=list[TicketListItem])
async def find_duplicates(
    ticket_id: int,
    q: str = Query(default="", max_length=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.agent)),
):
    ticket = await db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Заявка не найдена")

    query = select(Ticket).where(
        Ticket.id != ticket_id,
        Ticket.status.notin_([TicketStatus.merged, TicketStatus.resolved, TicketStatus.cancelled]),
    )
    if q:
        pattern = f"%{q}%"
        query = query.where(
            or_(Ticket.number.ilike(pattern), Ticket.title.ilike(pattern))
        )
    query = query.order_by(Ticket.created_at.desc()).limit(20)
    result = await db.execute(query)
    return [TicketListItem.model_validate(t) for t in result.scalars().all()]
