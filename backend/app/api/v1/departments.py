from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.department import Department
from app.models.user import User, UserRole
from app.schemas.department import DepartmentCreate, DepartmentUpdate, DepartmentResponse, DepartmentWithAgents, UserBrief
from app.utils.permissions import get_current_user, require_role

router = APIRouter()


@router.get("", response_model=list[DepartmentResponse])
async def list_departments(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    result = await db.execute(select(Department).order_by(Department.name))
    return result.scalars().all()


@router.post("", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
    data: DepartmentCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(UserRole.admin)),
):
    existing = await db.scalar(select(Department).where(Department.name == data.name))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Отдел с таким названием уже существует")

    dept = Department(name=data.name, description=data.description)
    db.add(dept)
    await db.commit()
    await db.refresh(dept)
    return dept


@router.get("/{dept_id}", response_model=DepartmentWithAgents)
async def get_department(
    dept_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    dept = await db.get(Department, dept_id)
    if not dept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Отдел не найден")

    agents_result = await db.execute(
        select(User).where(
            User.department_id == dept_id,
            User.role == UserRole.agent,
            User.is_active == True,  # noqa: E712
        )
    )
    agents = agents_result.scalars().all()

    return DepartmentWithAgents(
        id=dept.id,
        name=dept.name,
        description=dept.description,
        created_at=dept.created_at,
        agents=[UserBrief.model_validate(a) for a in agents],
    )


@router.put("/{dept_id}", response_model=DepartmentResponse)
async def update_department(
    dept_id: int,
    data: DepartmentUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(UserRole.admin)),
):
    dept = await db.get(Department, dept_id)
    if not dept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Отдел не найден")

    if data.name is not None and data.name != dept.name:
        existing = await db.scalar(select(Department).where(Department.name == data.name))
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Отдел с таким названием уже существует")
        dept.name = data.name

    if data.description is not None:
        dept.description = data.description

    await db.commit()
    await db.refresh(dept)
    return dept


@router.delete("/{dept_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_department(
    dept_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(UserRole.admin)),
):
    dept = await db.get(Department, dept_id)
    if not dept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Отдел не найден")

    # Проверка наличия заявок добавляется в Миссии 05 (tickets).
    # ON DELETE SET NULL на users.department_id обнуляет FK автоматически.

    await db.delete(dept)
    await db.commit()
