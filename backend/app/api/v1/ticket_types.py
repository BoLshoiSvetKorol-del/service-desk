from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.ticket_type import TicketType
from app.models.department import Department
from app.models.user import User, UserRole
from app.schemas.ticket_type import TicketTypeCreate, TicketTypeUpdate, TicketTypeResponse
from app.utils.permissions import get_current_user, require_role

router = APIRouter()


@router.get("", response_model=list[TicketTypeResponse])
async def list_ticket_types(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(TicketType).order_by(TicketType.name))
    return result.scalars().all()


@router.post("", response_model=TicketTypeResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket_type(
    data: TicketTypeCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(UserRole.admin)),
):
    existing = await db.scalar(select(TicketType).where(TicketType.name == data.name))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Тип заявки с таким названием уже существует")

    if data.default_department_id is not None:
        dept = await db.get(Department, data.default_department_id)
        if not dept:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Отдел не найден")

    tt = TicketType(
        name=data.name,
        service_type=data.service_type,
        work_direction=data.work_direction,
        default_department_id=data.default_department_id,
        is_active=data.is_active,
    )
    db.add(tt)
    await db.commit()
    await db.refresh(tt)
    return tt


@router.get("/{tt_id}", response_model=TicketTypeResponse)
async def get_ticket_type(
    tt_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    tt = await db.get(TicketType, tt_id)
    if not tt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тип заявки не найден")
    return tt


@router.put("/{tt_id}", response_model=TicketTypeResponse)
async def update_ticket_type(
    tt_id: int,
    data: TicketTypeUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(UserRole.admin)),
):
    tt = await db.get(TicketType, tt_id)
    if not tt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тип заявки не найден")

    if data.name is not None and data.name != tt.name:
        existing = await db.scalar(select(TicketType).where(TicketType.name == data.name))
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Тип заявки с таким названием уже существует")
        tt.name = data.name

    if data.service_type is not None:
        tt.service_type = data.service_type

    if data.work_direction is not None:
        tt.work_direction = data.work_direction

    if data.is_active is not None:
        tt.is_active = data.is_active

    if "default_department_id" in data.model_fields_set:
        if data.default_department_id is not None:
            dept = await db.get(Department, data.default_department_id)
            if not dept:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Отдел не найден")
        tt.default_department_id = data.default_department_id

    await db.commit()
    await db.refresh(tt)
    return tt


@router.delete("/{tt_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ticket_type(
    tt_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(UserRole.admin)),
):
    tt = await db.get(TicketType, tt_id)
    if not tt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тип заявки не найден")

    # Проверка наличия заявок добавляется в Миссии 05.
    await db.delete(tt)
    await db.commit()
