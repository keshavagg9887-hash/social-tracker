"""User Management Router [M3].

Provides admin-only endpoints for listing, creating, and modifying user accounts and roles.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.security import get_current_user, get_password_hash, require_roles
from ..database.models import User
from ..database.session import get_db
from .schemas import UserCreate, UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "",
    response_model=List[UserResponse],
    summary="List Users",
    description="Returns list of users with optional role filtering (requires handler or admin).",
)
async def list_users(
    role: Optional[str] = Query(None, description="Filter by role: admin, handler, viewer, authority"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "handler")),
) -> List[UserResponse]:
    stmt = select(User).order_by(User.created_at.desc())
    if role:
        stmt = stmt.where(User.role == role)
    result = await db.execute(stmt)
    users = result.scalars().all()
    return [UserResponse(**u.to_dict()) for u in users]


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get User by ID",
)
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    if current_user.role not in ("admin", "handler") and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")

    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse(**user.to_dict())


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create User (Admin only)",
)
async def create_user(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_roles("admin")),
) -> UserResponse:
    normalized_email = payload.email.lower().strip()
    stmt = select(User).where(User.email == normalized_email)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User email already exists")

    new_user = User(
        email=normalized_email,
        hashed_password=get_password_hash(payload.password),
        full_name=payload.full_name.strip(),
        role=payload.role,
        is_active=True,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return UserResponse(**new_user.to_dict())


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update User Role or Status (Admin only)",
)
async def update_user(
    user_id: str,
    payload: UserUpdate,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_roles("admin")),
) -> UserResponse:
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if payload.full_name is not None:
        user.full_name = payload.full_name.strip()
    if payload.role is not None:
        user.role = payload.role
    if payload.is_active is not None:
        user.is_active = payload.is_active

    await db.commit()
    await db.refresh(user)
    return UserResponse(**user.to_dict())


@router.delete(
    "/{user_id}",
    summary="Deactivate or Delete User (Admin only)",
)
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(require_roles("admin")),
):
    if user_id == admin_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete your own admin account")

    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    await db.delete(user)
    await db.commit()
    return {"status": "ok", "message": f"User {user_id} deleted successfully"}
