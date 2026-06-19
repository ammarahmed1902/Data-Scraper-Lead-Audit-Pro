#!/usr/bin/env python3
"""Create a user account. Usage: python -m scripts.create_user"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select

from app.core.database import async_session_factory
from app.core.security import UserRole, hash_password
from app.models.user import User


async def main() -> None:
    email = os.environ.get("USER_EMAIL", "ammarzerobyte@leadaudit.pro").lower()
    password = os.environ["USER_PASSWORD"]
    full_name = os.environ.get("USER_FULL_NAME", "Ammar")

    async with async_session_factory() as session:
        result = await session.execute(select(User).where(User.email == email))
        existing = result.scalar_one_or_none()

        if existing:
            existing.hashed_password = hash_password(password)
            existing.is_active = True
            existing.is_verified = True
            await session.commit()
            print(f"Updated password for existing user: {email}")
            return

        user = User(
            email=email,
            hashed_password=hash_password(password),
            full_name=full_name,
            role=UserRole.ADMIN.value,
            is_active=True,
            is_verified=True,
        )
        session.add(user)
        await session.commit()
        print(f"Created user: {email}")


if __name__ == "__main__":
    if "USER_PASSWORD" not in os.environ:
        print("Set USER_PASSWORD environment variable")
        sys.exit(1)
    asyncio.run(main())
