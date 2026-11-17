import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.dependencies import get_current_user, get_tenant_context, require_role, TenantContext
from backend.app.core.exceptions import PermissionDeniedError
from backend.app.db.enums import OrgRole
from backend.app.db.session import get_db_session
from backend.app.modules.auth.models import User
from backend.app.modules.organizations.models import Organization
from backend.app.modules.organizations.schemas import (
    MembershipCreateRequest,
    MembershipResponse,
    MembershipUpdateRequest,
    OrganizationCreateRequest,
    OrganizationResponse,
    OrganizationUpdateRequest,
)
from backend.app.modules.organizations.service import organization_service
from backend.app.schemas.common import ResponseEnvelope

router = APIRouter(tags=["Organizations"])


@router.post(
    "/",
    response_model=ResponseEnvelope[OrganizationResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new organization",
)
async def create_organization(
    payload: OrganizationCreateRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Creates a new organization tenant and assigns the authenticated creator as Administrator."""
    org = await organization_service.create_organization(session, payload, current_user)
    await session.commit()
    return ResponseEnvelope(
        data=OrganizationResponse.model_validate(org),
        message="Organization created successfully",
    )


@router.get(
    "/",
    response_model=ResponseEnvelope[List[OrganizationResponse]],
    summary="List organizations for authenticated user",
)
async def list_my_organizations(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Returns all organizations where the authenticated user is currently an active member."""
    orgs = await organization_service.list_user_organizations(session, current_user.id)
    return ResponseEnvelope(
        data=[OrganizationResponse.model_validate(o) for o in orgs],
    )


@router.get(
    "/{org_id}",
    response_model=ResponseEnvelope[OrganizationResponse],
    summary="Get organization details",
)
async def get_organization(
    org_id: uuid.UUID,
    context: TenantContext = Depends(get_tenant_context),
):
    """Retrieves metadata and status for the active organization."""
    if context.organization_id != org_id and not context.user.is_superuser:
        raise PermissionDeniedError("Cannot inspect foreign organization")
    org = await organization_service.get_organization(context.session, org_id)
    return ResponseEnvelope(data=OrganizationResponse.model_validate(org))


@router.patch(
    "/{org_id}",
    response_model=ResponseEnvelope[OrganizationResponse],
    summary="Update organization details",
)
async def update_organization(
    org_id: uuid.UUID,
    payload: OrganizationUpdateRequest,
    context: TenantContext = Depends(require_role(OrgRole.ORGANIZATION_ADMIN)),
):
    """Updates organization name or metadata. Requires Administrator role."""
    if context.organization_id != org_id and not context.user.is_superuser:
        raise PermissionDeniedError("Cannot modify foreign organization")
    org = await organization_service.update_organization(context.session, org_id, payload)
    await context.session.commit()
    return ResponseEnvelope(
        data=OrganizationResponse.model_validate(org),
        message="Organization updated successfully",
    )


@router.get(
    "/{org_id}/members",
    response_model=ResponseEnvelope[List[MembershipResponse]],
    summary="List organization members",
)
async def list_members(
    org_id: uuid.UUID,
    context: TenantContext = Depends(get_tenant_context),
):
    """Lists all members of the specified organization."""
    if context.organization_id != org_id and not context.user.is_superuser:
        raise PermissionDeniedError("Cannot access member list of foreign organization")
    members = await organization_service.member_repo.get_organization_members(
        context.session, org_id
    )
    return ResponseEnvelope(
        data=[MembershipResponse.model_validate(m) for m in members],
    )


@router.post(
    "/{org_id}/members",
    response_model=ResponseEnvelope[MembershipResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Add member to organization",
)
async def add_member(
    org_id: uuid.UUID,
    payload: MembershipCreateRequest,
    context: TenantContext = Depends(require_role(OrgRole.ORGANIZATION_ADMIN)),
):
    """Assigns an existing user to the organization with a designated role. Requires Admin."""
    if context.organization_id != org_id and not context.user.is_superuser:
        raise PermissionDeniedError("Cannot manage members of foreign organization")
    membership = await organization_service.add_member(context.session, org_id, payload)
    await context.session.commit()
    return ResponseEnvelope(
        data=MembershipResponse.model_validate(membership),
        message="Member added successfully",
    )


@router.patch(
    "/{org_id}/members/{user_id}",
    response_model=ResponseEnvelope[MembershipResponse],
    summary="Update member role",
)
async def update_member_role(
    org_id: uuid.UUID,
    user_id: uuid.UUID,
    payload: MembershipUpdateRequest,
    context: TenantContext = Depends(require_role(OrgRole.ORGANIZATION_ADMIN)),
):
    """Modifies a member's role. Requires Administrator role."""
    if context.organization_id != org_id and not context.user.is_superuser:
        raise PermissionDeniedError("Cannot modify member in foreign organization")
    membership = await organization_service.update_member_role(
        context.session, org_id, user_id, payload.role
    )
    await context.session.commit()
    return ResponseEnvelope(
        data=MembershipResponse.model_validate(membership),
        message="Member role updated successfully",
    )


@router.delete(
    "/{org_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove member from organization",
)
async def remove_member(
    org_id: uuid.UUID,
    user_id: uuid.UUID,
    context: TenantContext = Depends(require_role(OrgRole.ORGANIZATION_ADMIN)),
):
    """Removes a member from the organization. Requires Admin. Prevents removing the sole admin."""
    if context.organization_id != org_id and not context.user.is_superuser:
        raise PermissionDeniedError("Cannot modify member in foreign organization")
    await organization_service.remove_member(context.session, org_id, user_id)
    await context.session.commit()
