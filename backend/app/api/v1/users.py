"""
User management endpoints.
GET    /users          — List users (admin)
GET    /users/{id}     — Get user by ID
POST   /users          — Create user (admin)
PUT    /users/{id}     — Update user
DELETE /users/{id}     — Deactivate user (admin)
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import UserRole, get_current_user, require_role
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.user import UserCreate, UserListResponse, UserResponse, UserUpdate
from app.services.user_service import UserService

router = APIRouter()


@router.get("", response_model=PaginatedResponse[UserListResponse])
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    _payload: dict = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    return await service.list_users(page=page, page_size=page_size, search=search)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    _payload: dict = Depends(require_role(UserRole.MANAGER)),
    db: AsyncSession = Depends(get_db),
):
    actor_role = UserRole(current_user.role)
    if actor_role not in (UserRole.SUPER_ADMIN, UserRole.ADMIN) and user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only view your own profile",
        )
    service = UserService(db)
    return await service.get_user(user_id)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate,
    current_user: User = Depends(get_current_user),
    _payload: dict = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    return await service.create_user(data, UserRole(current_user.role))


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: uuid.UUID,
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    _payload: dict = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    return await service.update_user(user_id, data, current_user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    _payload: dict = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    await service.deactivate_user(user_id, current_user)
    return None
