import re
import uuid
from typing import Any, Dict, Optional
from pydantic import Field, model_validator

from backend.app.db.enums import OrgRole
from backend.app.modules.auth.schemas import UserResponse
from backend.app.schemas.common import BaseSchema, TimestampSchema


def slugify(text: str) -> str:
    """Converts a name into a URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


class OrganizationCreateRequest(BaseSchema):
    """Payload for creating a new tenant organization."""
    name: str = Field(min_length=2, max_length=255, description="Organization display name")
    slug: Optional[str] = Field(None, min_length=2, max_length=64, description="Unique URL slug")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata attributes")

    @model_validator(mode="after")
    def compute_slug(self) -> "OrganizationCreateRequest":
        if not self.slug:
            self.slug = slugify(self.name)
        else:
            self.slug = slugify(self.slug)
        return self


class OrganizationUpdateRequest(BaseSchema):
    """Payload for updating organization details."""
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    is_active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class OrganizationResponse(TimestampSchema):
    """Public organization representation."""
    id: uuid.UUID
    name: str
    slug: str
    is_active: bool
    metadata_: Dict[str, Any] = Field(
        default_factory=dict,
        validation_alias="metadata_",
        serialization_alias="metadata",
    )


class MembershipCreateRequest(BaseSchema):
    """Payload for adding a user to an organization."""
    user_id: uuid.UUID
    role: OrgRole = OrgRole.INVESTIGATOR


class MembershipUpdateRequest(BaseSchema):
    """Payload for modifying a member's role."""
    role: OrgRole


class MembershipResponse(TimestampSchema):
    """Public organization membership representation."""
    organization_id: uuid.UUID
    user_id: uuid.UUID
    role: OrgRole
    user: Optional[UserResponse] = None
