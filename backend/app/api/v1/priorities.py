from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.priority import Priority
from app.models.user import User
from app.schemas.ticket_type import PriorityResponse
from app.utils.permissions import get_current_user

router = APIRouter()


@router.get("", response_model=list[PriorityResponse])
async def list_priorities(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Priority).order_by(Priority.id))
    return result.scalars().all()
