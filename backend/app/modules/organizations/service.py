import uuid
from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.exceptions import ConflictError, NotFoundError, PermissionDeniedError
from backend.app.db.enums import OrgRole
from backend.app.modules.auth.models import User
from backend.app.modules.auth.repository import user_repository
from backend.app.modules.organizations.models import Membership, Organization
from backend.app.modules.organizations.repository import (
    membership_repository,
    organization_repository,
)
from backend.app.modules.organizations.schemas import (
    MembershipCreateRequest,
    OrganizationCreateRequest,
    OrganizationUpdateRequest,
)


class OrganizationService:
    """Domain service managing multi-tenant organization lifecycle and membership RBAC."""

    def __init__(
        self,
        org_repo=organization_repository,
        member_repo=membership_repository,
        user_repo=user_repository,
    ):
        self.org_repo = org_repo
        self.member_repo = member_repo
        self.user_repo = user_repo

    async def create_organization(
        self,
        session: AsyncSession,
        data: OrganizationCreateRequest,
        creator: User,
    ) -> Organization:
        """Creates a new organization and assigns the creator as initial Administrator."""
        existing_slug = await self.org_repo.get_by_slug(session, data.slug)
        if existing_slug:
            raise ConflictError(f"Organization slug '{data.slug}' is already taken")

        existing_name = await self.org_repo.get_by_name(session, data.name)
        if existing_name:
            raise ConflictError(f"Organization name '{data.name}' already exists")

        org = await self.org_repo.create(
            session,
            obj_in={
                "name": data.name.strip(),
                "slug": data.slug,
                "metadata_": data.metadata,
                "is_active": True,
            },
        )

        # Creator automatically becomes Admin
        await self.member_repo.create(
            session,
            obj_in={
                "organization_id": org.id,
                "user_id": creator.id,
                "role": OrgRole.ORGANIZATION_ADMIN,
            },
        )

        return org

    async def get_organization(
        self, session: AsyncSession, organization_id: uuid.UUID
    ) -> Organization:
        """Retrieves an organization by ID."""
        org = await self.org_repo.get(session, organization_id)
        if not org or not org.is_active:
            raise NotFoundError("Organization", organization_id)
        return org

    async def list_user_organizations(
        self, session: AsyncSession, user_id: uuid.UUID
    ) -> List[Organization]:
        """Lists all organizations where the given user holds an active membership."""
        return await self.org_repo.get_user_organizations(session, user_id)

    async def update_organization(
        self,
        session: AsyncSession,
        organization_id: uuid.UUID,
        data: OrganizationUpdateRequest,
    ) -> Organization:
        """Updates organization details (e.g. name, metadata)."""
        org = await self.get_organization(session, organization_id)

        update_dict = {}
        if data.name is not None:
            existing = await self.org_repo.get_by_name(session, data.name)
            if existing and existing.id != org.id:
                raise ConflictError(f"Organization name '{data.name}' is already taken")
            update_dict["name"] = data.name.strip()
        if data.is_active is not None:
            update_dict["is_active"] = data.is_active
        if data.metadata is not None:
            update_dict["metadata_"] = data.metadata

        return await self.org_repo.update(session, db_obj=org, obj_in=update_dict)

    async def add_member(
        self,
        session: AsyncSession,
        organization_id: uuid.UUID,
        data: MembershipCreateRequest,
    ) -> Membership:
        """Adds a registered user to the organization with a designated role."""
        org = await self.get_organization(session, organization_id)

        target_user = await self.user_repo.get(session, data.user_id)
        if not target_user:
            raise NotFoundError("User", data.user_id)

        existing_membership = await self.member_repo.get_membership(
            session, organization_id, data.user_id
        )
        if existing_membership:
            raise ConflictError("User is already a member of this organization")

        membership = await self.member_repo.create(
            session,
            obj_in={
                "organization_id": org.id,
                "user_id": target_user.id,
                "role": data.role,
            },
        )
        membership.user = target_user
        return membership

    async def update_member_role(
        self,
        session: AsyncSession,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        new_role: OrgRole,
    ) -> Membership:
        """Updates a member's organizational role."""
        membership = await self.member_repo.get_membership(
            session, organization_id, user_id
        )
        if not membership:
            raise NotFoundError("Membership", f"{organization_id}:{user_id}")

        membership.role = new_role
        session.add(membership)
        await session.flush()
        target_user = await self.user_repo.get(session, user_id)
        membership.user = target_user
        return membership

    async def remove_member(
        self,
        session: AsyncSession,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        """Removes a user from the organization, preventing removal of the sole admin."""
        membership = await self.member_repo.get_membership(
            session, organization_id, user_id
        )
        if not membership:
            raise NotFoundError("Membership", f"{organization_id}:{user_id}")

        if membership.role == OrgRole.ORGANIZATION_ADMIN:
            # Check count of remaining admins
            admin_count_query = (
                select(func.count())
                .select_from(Membership)
                .where(
                    Membership.organization_id == organization_id,
                    Membership.role == OrgRole.ORGANIZATION_ADMIN,
                )
            )
            count = (await session.execute(admin_count_query)).scalar() or 0
            if count <= 1:
                raise ConflictError("Cannot remove the sole administrator of an organization")

        await session.delete(membership)
        await session.flush()


organization_service = OrganizationService()
