import uuid
from typing import Optional
from pydantic import EmailStr, Field

from backend.app.schemas.common import BaseSchema, TimestampSchema


class UserRegisterRequest(BaseSchema):
    """Payload for registering a new user account."""
    email: EmailStr
    password: str = Field(min_length=8, max_length=128, description="Plaintext password (min 8 chars)")
    full_name: str = Field(min_length=1, max_length=255, description="Full name of the user")


class UserLoginRequest(BaseSchema):
    """Payload for user authentication."""
    email: EmailStr
    password: str = Field(min_length=1, description="Account password")


class TokenRefreshRequest(BaseSchema):
    """Payload for rotating token refresh."""
    refresh_token: str = Field(description="Cryptographically valid refresh token")


class UserResponse(TimestampSchema):
    """Public user identity representation."""
    id: uuid.UUID
    email: EmailStr
    full_name: str
    is_active: bool
    is_superuser: bool


class TokenResponse(BaseSchema):
    """Authentication token response envelope."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Access token lifespan in seconds")
    user: UserResponse
