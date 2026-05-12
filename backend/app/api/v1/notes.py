from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.ticket import Ticket
from app.models.ticket_note import TicketNote
from app.models.user import User, UserRole
from app.schemas.tag import TicketNoteCreate, TicketNoteUpdate, TicketNoteResponse
from app.services.ticket_service import _check_ticket_access
from app.utils.permissions import require_role

router = APIRouter()


@router.get("/tickets/{ticket_id}/notes", response_model=list[TicketNoteResponse])
async def list_notes(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.agent)),
):
    ticket = await db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    _check_ticket_access(ticket, current_user)

    result = await db.execute(
        select(TicketNote)
        .where(TicketNote.ticket_id == ticket_id, TicketNote.author_id == current_user.id)
        .order_by(TicketNote.created_at)
    )
    return [TicketNoteResponse.model_validate(n) for n in result.scalars().all()]


@router.post("/tickets/{ticket_id}/notes", response_model=TicketNoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(
    ticket_id: int,
    data: TicketNoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.agent)),
):
    ticket = await db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    _check_ticket_access(ticket, current_user)

    note = TicketNote(ticket_id=ticket_id, author_id=current_user.id, body=data.body)
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return TicketNoteResponse.model_validate(note)


@router.put("/tickets/{ticket_id}/notes/{note_id}", response_model=TicketNoteResponse)
async def update_note(
    ticket_id: int,
    note_id: int,
    data: TicketNoteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.agent)),
):
    note = await db.get(TicketNote, note_id)
    if not note or note.ticket_id != ticket_id:
        raise HTTPException(status_code=404, detail="Заметка не найдена")
    if note.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Нельзя редактировать чужую заметку")

    note.body = data.body
    await db.commit()
    await db.refresh(note)
    return TicketNoteResponse.model_validate(note)


@router.delete("/tickets/{ticket_id}/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    ticket_id: int,
    note_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.agent)),
):
    note = await db.get(TicketNote, note_id)
    if not note or note.ticket_id != ticket_id:
        raise HTTPException(status_code=404, detail="Заметка не найдена")
    if note.author_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Нельзя удалить чужую заметку")

    await db.delete(note)
    await db.commit()
