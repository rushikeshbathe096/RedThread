import uuid
from typing import Any, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.modules.organizations.models import Membership, Organization
from backend.app.repositories.base import BaseRepository


class OrganizationRepository(BaseRepository[Organization, Any, Any]):
    def __init__(self):
        super().__init__(Organization)

    async def get_by_slug(
        self, session: AsyncSession, slug: str
    ) -> Optional[Organization]:
        """Fetch organization by URL slug."""
        result = await session.execute(
            select(Organization).where(Organization.slug == slug.lower().strip())
        )
        return result.scalars().first()

    async def get_by_name(
        self, session: AsyncSession, name: str
    ) -> Optional[Organization]:
        """Fetch organization by exact name."""
        result = await session.execute(
            select(Organization).where(Organization.name == name.strip())
        )
        return result.scalars().first()

    async def get_user_organizations(
        self, session: AsyncSession, user_id: uuid.UUID
    ) -> List[Organization]:
        """Fetch all organizations a user is currently a member of."""
        query = (
            select(Organization)
            .join(Membership, Membership.organization_id == Organization.id)
            .where(Membership.user_id == user_id, Organization.is_active.is_(True))
            .order_by(Organization.name)
        )
        result = await session.execute(query)
        return list(result.scalars().all())


class MembershipRepository(BaseRepository[Membership, Any, Any]):
    def __init__(self):
        super().__init__(Membership)

    async def get_membership(
        self, session: AsyncSession, organization_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[Membership]:
        """Look up user membership in an organization."""
        result = await session.execute(
            select(Membership).where(
                Membership.organization_id == organization_id,
                Membership.user_id == user_id,
            )
        )
        return result.scalars().first()

    async def get_organization_members(
        self, session: AsyncSession, organization_id: uuid.UUID
    ) -> List[Membership]:
        """List all members of an organization with eager-loaded user accounts."""
        query = (
            select(Membership)
            .options(selectinload(Membership.user))
            .where(Membership.organization_id == organization_id)
            .order_by(Membership.created_at)
        )
        result = await session.execute(query)
        return list(result.scalars().all())


organization_repository = OrganizationRepository()
membership_repository = MembershipRepository()
