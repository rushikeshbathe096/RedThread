import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.core.exceptions import AuthenticationError, ConflictError, NotFoundError
from backend.app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from backend.app.modules.auth.models import User
from backend.app.modules.auth.repository import user_repository
from backend.app.modules.auth.schemas import (
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)


class AuthService:
    """Domain service managing user registration, authentication, and session tokens."""

    def __init__(self, repo=user_repository):
        self.repo = repo

    async def register_user(
        self, session: AsyncSession, data: UserRegisterRequest
    ) -> User:
        """Registers a new user account, validating email uniqueness and hashing password."""
        existing = await self.repo.get_by_email(session, data.email)
        if existing:
            raise ConflictError(f"Email '{data.email}' is already registered")

        password_hash = get_password_hash(data.password)
        user = await self.repo.create(
            session,
            obj_in={
                "email": data.email.lower().strip(),
                "password_hash": password_hash,
                "full_name": data.full_name.strip(),
                "is_active": True,
                "is_superuser": False,
            },
        )
        return user

    async def authenticate_user(
        self, session: AsyncSession, data: UserLoginRequest
    ) -> User:
        """Verifies credentials and returns the active User entity."""
        user = await self.repo.get_by_email(session, data.email)
        if not user or not user.is_active:
            raise AuthenticationError("Invalid email or password")

        if not verify_password(data.password, user.password_hash):
            raise AuthenticationError("Invalid email or password")

        return user

    def generate_token_response(
        self,
        user: User,
        org_id: Optional[uuid.UUID] = None,
        role: Optional[str] = None,
    ) -> TokenResponse:
        """Issues an access token and refresh token pair for an authenticated user."""
        access_token = create_access_token(
            subject=user.id,
            org_id=org_id,
            role=role,
        )
        refresh_token = create_refresh_token(subject=user.id)
        expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=expires_in,
            user=UserResponse.model_validate(user),
        )

    async def refresh_tokens(
        self, session: AsyncSession, refresh_token: str
    ) -> TokenResponse:
        """Validates a refresh token and returns a fresh access/refresh token pair."""
        payload = decode_token(refresh_token, expected_type="refresh")
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise AuthenticationError("Malformed refresh token")

        try:
            user_id = uuid.UUID(user_id_str)
        except ValueError:
            raise AuthenticationError("Invalid user identity in token")

        user = await self.repo.get(session, user_id)
        if not user or not user.is_active:
            raise AuthenticationError("User account no longer active")

        return self.generate_token_response(user)


auth_service = AuthService()
