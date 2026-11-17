import uuid
from typing import Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.modules.auth.models import User
from backend.app.modules.organizations.models import Membership
from backend.app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User, Any, Any]):
    def __init__(self):
        super().__init__(User)

    async def get_by_email(self, session: AsyncSession, email: str) -> Optional[User]:
        """Look up an active or inactive user by lowercase email."""
        result = await session.execute(
            select(User).where(User.email == email.lower().strip())
        )
        return result.scalars().first()

    async def get_by_id_with_memberships(
        self, session: AsyncSession, user_id: uuid.UUID
    ) -> Optional[User]:
        """Fetch user with eager-loaded memberships and organization details."""
        result = await session.execute(
            select(User)
            .options(
                selectinload(User.memberships).selectinload(Membership.organization)
            )
            .where(User.id == user_id)
        )
        return result.scalars().first()


user_repository = UserRepository()
