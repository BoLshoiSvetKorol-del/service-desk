from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import redis.asyncio as aioredis

from app.database import get_db
from app.models.comment import Comment
from app.models.ticket import Ticket
from app.models.user import User, UserRole
from app.schemas.comment import CommentCreate, CommentUpdate, CommentResponse
from app.services.ticket_service import _check_ticket_access
from app.services.notification_service import notify_ticket_event
from app.redis import get_redis
from app.utils.permissions import get_current_user, require_role

router = APIRouter()

EDIT_WINDOW = timedelta(minutes=5)


async def _get_ticket_or_404(db: AsyncSession, ticket_id: int) -> Ticket:
    ticket = await db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    return ticket


async def _get_comment_or_404(db: AsyncSession, ticket_id: int, comment_id: int) -> Comment:
    comment = await db.get(Comment, comment_id)
    if not comment or comment.ticket_id != ticket_id:
        raise HTTPException(status_code=404, detail="Комментарий не найден")
    return comment


@router.get("/{ticket_id}/comments", response_model=list[CommentResponse])
async def list_comments(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = await _get_ticket_or_404(db, ticket_id)
    _check_ticket_access(ticket, current_user)

    result = await db.execute(
        select(Comment)
        .where(Comment.ticket_id == ticket_id)
        .order_by(Comment.created_at)
    )
    comments = result.scalars().all()

    if current_user.role == UserRole.user:
        comments = [c for c in comments if not c.is_internal]

    return [CommentResponse.model_validate(c) for c in comments]


@router.post("/{ticket_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    ticket_id: int,
    data: CommentCreate,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    current_user: User = Depends(get_current_user),
):
    ticket = await _get_ticket_or_404(db, ticket_id)
    _check_ticket_access(ticket, current_user)

    if data.is_internal and current_user.role == UserRole.user:
        raise HTTPException(status_code=403, detail="Пользователи не могут создавать внутренние комментарии")

    comment = Comment(
        ticket_id=ticket_id,
        author_id=current_user.id,
        body=data.body,
        is_internal=data.is_internal,
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)

    # Email заявителю о новом (публичном) комментарии
    if not data.is_internal:
        try:
            from app.tasks.email_tasks import send_email_task
            requester = await db.get(User, ticket.requester_id)
            if requester and requester.id != current_user.id:
                send_email_task.delay(
                    to=requester.email,
                    template="new_comment.html",
                    context={
                        "recipient_name": requester.full_name,
                        "ticket_number": ticket.number,
                        "comment_body": data.body,
                        "author_name": current_user.full_name,
                        "created_at": comment.created_at.strftime("%d.%m.%Y %H:%M UTC"),
                    },
                    subject=f"Новый комментарий к заявке {ticket.number}",
                )
        except Exception:
            pass

    # SSE + уведомление в БД
    if not data.is_internal:
        await notify_ticket_event(db, redis, ticket, "new_comment", current_user)

    return CommentResponse.model_validate(comment)


@router.put("/{ticket_id}/comments/{comment_id}", response_model=CommentResponse)
async def update_comment(
    ticket_id: int,
    comment_id: int,
    data: CommentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = await _get_ticket_or_404(db, ticket_id)
    _check_ticket_access(ticket, current_user)
    comment = await _get_comment_or_404(db, ticket_id, comment_id)

    if comment.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Можно редактировать только свои комментарии")

    created = comment.created_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) - created > EDIT_WINDOW:
        raise HTTPException(status_code=403, detail="Окно редактирования истекло (5 минут)")

    comment.body = data.body
    await db.commit()
    await db.refresh(comment)
    return CommentResponse.model_validate(comment)


@router.delete("/{ticket_id}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    ticket_id: int,
    comment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = await _get_ticket_or_404(db, ticket_id)
    _check_ticket_access(ticket, current_user)
    comment = await _get_comment_or_404(db, ticket_id, comment_id)

    is_author_in_window = (
        comment.author_id == current_user.id
        and _within_edit_window(comment.created_at)
    )
    if current_user.role != UserRole.admin and not is_author_in_window:
        raise HTTPException(status_code=403, detail="Нет прав на удаление комментария")

    await db.delete(comment)
    await db.commit()


def _within_edit_window(created_at: datetime) -> bool:
    ts = created_at
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - ts <= EDIT_WINDOW
