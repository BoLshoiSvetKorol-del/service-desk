from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from app.database import get_db
from app.models.ticket import Ticket, TicketStatus
from app.models.ticket_rating import TicketRating
from app.models.user import User, UserRole
from app.services.ticket_service import _check_ticket_access
from app.utils.permissions import get_current_user

router = APIRouter()


class RatingCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: str | None = None


class RatingResponse(BaseModel):
    id: int
    ticket_id: int
    rating: int
    comment: str | None = None
    created_at: str

    model_config = {"from_attributes": True}


@router.post(
    "/tickets/{ticket_id}/rating",
    response_model=RatingResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["ratings"],
)
async def submit_rating(
    ticket_id: int,
    data: RatingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = await db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    _check_ticket_access(ticket, current_user)

    # Только заявитель может оставить оценку
    if current_user.role != UserRole.user or ticket.requester_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Оценку может оставить только автор обращения",
        )

    # Только для выполненных заявок
    if ticket.status != TicketStatus.resolved:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Оценку можно оставить только для выполненных инцидентов",
        )

    # Upsert: одна оценка на заявку
    existing = await db.scalar(
        select(TicketRating).where(TicketRating.ticket_id == ticket_id)
    )
    if existing:
        existing.rating = data.rating
        existing.comment = data.comment
        await db.commit()
        await db.refresh(existing)
        return RatingResponse(
            id=existing.id,
            ticket_id=existing.ticket_id,
            rating=existing.rating,
            comment=existing.comment,
            created_at=existing.created_at.isoformat(),
        )

    rating = TicketRating(
        ticket_id=ticket_id,
        user_id=current_user.id,
        rating=data.rating,
        comment=data.comment,
    )
    db.add(rating)
    await db.commit()
    await db.refresh(rating)
    return RatingResponse(
        id=rating.id,
        ticket_id=rating.ticket_id,
        rating=rating.rating,
        comment=rating.comment,
        created_at=rating.created_at.isoformat(),
    )


@router.get(
    "/tickets/{ticket_id}/rating",
    response_model=RatingResponse | None,
    tags=["ratings"],
)
async def get_rating(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = await db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    _check_ticket_access(ticket, current_user)

    rating = await db.scalar(
        select(TicketRating).where(TicketRating.ticket_id == ticket_id)
    )
    if not rating:
        return None
    return RatingResponse(
        id=rating.id,
        ticket_id=rating.ticket_id,
        rating=rating.rating,
        comment=rating.comment,
        created_at=rating.created_at.isoformat(),
    )
