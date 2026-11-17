import uuid
from dataclasses import dataclass
from typing import Callable, List, Optional

from fastapi import Depends, Header, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.exceptions import (
    AuthenticationError,
    PermissionDeniedError,
    ValidationError,
)
from backend.app.core.security import decode_token
from backend.app.db.enums import OrgRole
from backend.app.db.session import get_db_session, set_session_tenant_context
from backend.app.modules.auth.models import User
from backend.app.modules.auth.repository import user_repository
from backend.app.modules.organizations.repository import (
    membership_repository,
    organization_repository,
)

http_bearer = HTTPBearer(auto_error=False)


@dataclass
class TenantContext:
    """Encapsulates the authenticated user, current organization tenant, and RBAC role."""
    user: User
    organization_id: uuid.UUID
    role: OrgRole
    session: AsyncSession


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
    session: AsyncSession = Depends(get_db_session),
) -> User:
    """Validates the Authorization Bearer token and returns the authenticated User entity."""
    if not credentials or not credentials.credentials:
        raise AuthenticationError("Authentication token is required")

    payload = decode_token(credentials.credentials, expected_type="access")
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise AuthenticationError("Invalid authentication token payload")

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise AuthenticationError("Malformed user identifier in token")

    user = await user_repository.get(session, user_id)
    if not user or not user.is_active:
        raise AuthenticationError("User account is inactive or not found")

    return user


async def get_tenant_context(
    request: Request,
    user: User = Depends(get_current_user),
    org_header: Optional[str] = Header(None, alias="X-Organization-ID"),
    session: AsyncSession = Depends(get_db_session),
) -> TenantContext:
    """
    Extracts the active organization context, validates membership, and activates
    transaction-local PostgreSQL session variables for Row-Level Security (RLS).
    """
    target_org_id: Optional[uuid.UUID] = None

    if org_header:
        try:
            target_org_id = uuid.UUID(org_header.strip())
        except ValueError:
            raise ValidationError("Invalid X-Organization-ID header format; UUID expected")
    else:
        # If user only belongs to one organization, infer it
        user_orgs = await organization_repository.get_user_organizations(session, user.id)
        if len(user_orgs) == 1:
            target_org_id = user_orgs[0].id
        elif len(user_orgs) == 0:
            raise PermissionDeniedError("User does not belong to any active organization")
        else:
            raise ValidationError(
                "Multiple organizations available; specify target organization via X-Organization-ID header"
            )

    membership = await membership_repository.get_membership(session, target_org_id, user.id)
    if not membership:
        raise PermissionDeniedError(
            f"User does not have access to organization '{target_org_id}'"
        )

    # Activate transaction-local RLS variables in PostgreSQL
    await set_session_tenant_context(
        session=session,
        org_id=target_org_id,
        user_id=user.id,
        is_worker=False,
    )

    return TenantContext(
        user=user,
        organization_id=target_org_id,
        role=membership.role,
        session=session,
    )


def require_role(*allowed_roles: OrgRole) -> Callable[[TenantContext], TenantContext]:
    """Dependency factory enforcing organizational Role-Based Access Control (RBAC)."""
    async def role_checker(
        context: TenantContext = Depends(get_tenant_context),
    ) -> TenantContext:
        if context.user.is_superuser:
            return context
        if context.role not in allowed_roles:
            raise PermissionDeniedError(
                f"Role '{context.role.value}' lacks required permissions for this action. "
                f"Requires one of: {[r.value for r in allowed_roles]}"
            )
        return context

    return role_checker
