from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.saved_filter import SavedFilter
from app.models.user import User
from app.schemas.report import SavedFilterCreate, SavedFilterResponse
from app.utils.permissions import get_current_user

router = APIRouter()


@router.get("", response_model=list[SavedFilterResponse])
async def list_filters(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(SavedFilter)
        .where(SavedFilter.user_id == current_user.id)
        .order_by(SavedFilter.created_at.desc())
    )
    return [SavedFilterResponse.model_validate(f) for f in result.scalars().all()]


@router.post("", response_model=SavedFilterResponse, status_code=status.HTTP_201_CREATED)
async def create_filter(
    data: SavedFilterCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    saved = SavedFilter(
        user_id=current_user.id,
        name=data.name,
        filter_params=data.filter_params,
    )
    db.add(saved)
    await db.commit()
    await db.refresh(saved)
    return SavedFilterResponse.model_validate(saved)


@router.delete("/{filter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_filter(
    filter_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    saved = await db.get(SavedFilter, filter_id)
    if not saved:
        raise HTTPException(status_code=404, detail="Фильтр не найден")
    if saved.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Нет доступа к этому фильтру")
    await db.delete(saved)
    await db.commit()
