from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.tag import Tag
from app.models.ticket import Ticket
from app.models.user import User, UserRole
from app.schemas.tag import TagCreate, TagResponse, SetTagsRequest
from app.utils.permissions import get_current_user, require_role

router = APIRouter()


@router.get("", response_model=list[TagResponse])
async def list_tags(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Tag).order_by(Tag.name))
    return [TagResponse.model_validate(t) for t in result.scalars().all()]


@router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    data: TagCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.department_head, UserRole.agent)),
):
    existing = await db.scalar(select(Tag).where(Tag.name == data.name))
    if existing:
        raise HTTPException(status_code=409, detail="Тег с таким именем уже существует")
    tag = Tag(name=data.name, color_hex=data.color_hex)
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    return TagResponse.model_validate(tag)


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    tag = await db.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Тег не найден")
    await db.delete(tag)
    await db.commit()


@router.put("/tickets/{ticket_id}/tags", response_model=list[TagResponse])
async def set_ticket_tags(
    ticket_id: int,
    data: SetTagsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.department_head, UserRole.agent)),
):
    ticket = await db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Заявка не найдена")

    tags = []
    for tid in data.tag_ids:
        tag = await db.get(Tag, tid)
        if not tag:
            raise HTTPException(status_code=404, detail=f"Тег {tid} не найден")
        tags.append(tag)

    await db.refresh(ticket, ["tags"])
    ticket.tags = tags
    await db.commit()
    await db.refresh(ticket, ["tags"])
    return [TagResponse.model_validate(t) for t in ticket.tags]
