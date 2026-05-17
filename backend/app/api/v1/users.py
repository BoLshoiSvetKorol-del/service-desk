from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from app.database import get_db
from app.models.user import User, UserRole
from app.models.department import Department
from app.schemas.user import UserCreate, UserUpdate, UserMeUpdate, UserResponse
from app.utils.pagination import PagedResponse
from app.utils.permissions import get_current_user, require_role
from app.utils.security import hash_password

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_me(
    data: UserMeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if data.email is not None and data.email != current_user.email:
        existing = await db.scalar(select(User).where(User.email == data.email, User.id != current_user.id))
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email уже используется")
        current_user.email = data.email

    if data.full_name is not None:
        current_user.full_name = data.full_name

    if data.password is not None:
        current_user.password_hash = hash_password(data.password)

    if "phone" in data.model_fields_set:
        current_user.phone = data.phone

    if "contact_info" in data.model_fields_set:
        current_user.contact_info = data.contact_info

    await db.commit()
    await db.refresh(current_user)
    return UserResponse.model_validate(current_user)


@router.get("", response_model=PagedResponse[UserResponse])
async def list_users(
    role: UserRole | None = Query(default=None),
    department_id: int | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    search: str | None = Query(default=None, max_length=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.department_head, UserRole.agent)),
):
    query = select(User)

    if role is not None:
        query = query.where(User.role == role)
    if department_id is not None:
        query = query.where(User.department_id == department_id)
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    if search:
        pattern = f"%{search}%"
        query = query.where(
            or_(
                User.username.ilike(pattern),
                User.full_name.ilike(pattern),
                User.email.ilike(pattern),
            )
        )

    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    result = await db.execute(
        query.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    )
    users = result.scalars().all()

    return PagedResponse.build(
        items=[UserResponse.model_validate(u) for u in users],
        total=total or 0,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(UserRole.admin)),
):
    existing_email = await db.scalar(select(User).where(User.email == data.email))
    if existing_email:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email уже используется")

    existing_username = await db.scalar(select(User).where(User.username == data.username))
    if existing_username:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username уже используется")

    if data.department_id is not None:
        dept = await db.get(Department, data.department_id)
        if not dept:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Отдел не найден")

    user = User(
        email=data.email,
        username=data.username,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        role=data.role,
        department_id=data.department_id,
        is_active=True,
        is_email_verified=True,  # admin-created users are pre-verified
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return UserResponse.model_validate(user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in (UserRole.admin, UserRole.department_head, UserRole.agent):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав")

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    return UserResponse.model_validate(user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(UserRole.admin)),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    if data.email is not None and data.email != user.email:
        existing = await db.scalar(select(User).where(User.email == data.email, User.id != user_id))
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email уже используется")
        user.email = data.email

    if data.full_name is not None:
        user.full_name = data.full_name

    if data.password is not None:
        user.password_hash = hash_password(data.password)

    if data.role is not None:
        user.role = data.role

    if data.department_id is not None:
        dept = await db.get(Department, data.department_id)
        if not dept:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Отдел не найден")
        user.department_id = data.department_id
    elif "department_id" in data.model_fields_set and data.department_id is None:
        user.department_id = None

    await db.commit()
    await db.refresh(user)
    return UserResponse.model_validate(user)


@router.patch("/{user_id}/activate", response_model=UserResponse)
async def toggle_activate(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Нельзя деактивировать самого себя")

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    user.is_active = not user.is_active
    await db.commit()
    await db.refresh(user)
    return UserResponse.model_validate(user)
