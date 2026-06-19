#!/usr/bin/env python3
"""
Seed super admin user.
Usage: python -m scripts.seed_admin
"""

import asyncio
import os
import sys

# Allow running from backend directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select

from app.core.database import async_session_factory
from app.core.security import UserRole, hash_password
from app.models.user import User


async def seed_admin() -> None:
    email = os.environ.get("SEED_ADMIN_EMAIL", "admin@leadaudit.pro")
    password = os.environ.get("SEED_ADMIN_PASSWORD", "Admin123!ChangeMe")
    full_name = os.environ.get("SEED_ADMIN_NAME", "Super Admin")

    async with async_session_factory() as session:
        result = await session.execute(select(User).where(User.email == email.lower()))
        existing = result.scalar_one_or_none()

        if existing:
            print(f"Admin user already exists: {email}")
            return

        user = User(
            email=email.lower(),
            hashed_password=hash_password(password),
            full_name=full_name,
            role=UserRole.SUPER_ADMIN.value,
            is_active=True,
            is_verified=True,
        )
        session.add(user)
        await session.commit()
        print(f"Super admin created: {email}")
        print("Change the default password immediately in production.")


if __name__ == "__main__":
    asyncio.run(seed_admin())
