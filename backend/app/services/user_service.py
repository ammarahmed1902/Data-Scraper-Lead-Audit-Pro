"""User management business logic."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import can_assign_role, can_modify_user
from app.core.security import UserRole, hash_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.common import PaginatedResponse
from app.schemas.user import UserCreate, UserListResponse, UserResponse, UserUpdate


class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)

    async def list_users(
        self,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
    ) -> PaginatedResponse[UserListResponse]:
        skip = (page - 1) * page_size
        users = await self.user_repo.list_users(skip=skip, limit=page_size, search=search)
        total = await self.user_repo.count_users(search=search)
        total_pages = max(1, (total + page_size - 1) // page_size)
        return PaginatedResponse(
            items=[UserListResponse.model_validate(u) for u in users],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def get_user(self, user_id: uuid.UUID) -> UserResponse:
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return UserResponse.model_validate(user)

    async def create_user(
        self,
        data: UserCreate,
        actor_role: UserRole,
    ) -> UserResponse:
        if not can_assign_role(actor_role, data.role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Cannot assign role: {data.role.value}",
            )

        existing = await self.user_repo.get_by_email(data.email.lower())
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        user = User(
            email=data.email.lower(),
            hashed_password=hash_password(data.password),
            full_name=data.full_name.strip(),
            role=data.role.value,
            phone=data.phone,
            timezone=data.timezone,
            is_active=True,
            is_verified=True,
        )
        user = await self.user_repo.create(user)
        return UserResponse.model_validate(user)

    async def update_user(
        self,
        user_id: uuid.UUID,
        data: UserUpdate,
        actor: User,
    ) -> UserResponse:
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        actor_role = UserRole(actor.role)
        target_role = UserRole(user.role)

        if user.id != actor.id and not can_modify_user(actor_role, target_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot modify this user",
            )

        if data.role is not None:
            if user.id == actor.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot change your own role",
                )
            if not can_assign_role(actor_role, data.role):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Cannot assign role: {data.role.value}",
                )
            user.role = data.role.value

        if data.email is not None:
            email = data.email.lower()
            existing = await self.user_repo.get_by_email(email)
            if existing and existing.id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email already in use",
                )
            user.email = email

        if data.full_name is not None:
            user.full_name = data.full_name.strip()
        if data.phone is not None:
            user.phone = data.phone
        if data.timezone is not None:
            user.timezone = data.timezone
        if data.is_active is not None:
            if user.id == actor.id and not data.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot deactivate your own account",
                )
            user.is_active = data.is_active

        user = await self.user_repo.update(user)
        return UserResponse.model_validate(user)

    async def deactivate_user(
        self,
        user_id: uuid.UUID,
        actor: User,
    ) -> None:
        if user_id == actor.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot deactivate your own account",
            )

        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        actor_role = UserRole(actor.role)
        if not can_modify_user(actor_role, UserRole(user.role)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot deactivate this user",
            )

        user.is_active = False
        await self.user_repo.update(user)
