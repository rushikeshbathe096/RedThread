from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.dependencies import get_current_user
from backend.app.db.session import get_db_session
from backend.app.modules.auth.models import User
from backend.app.modules.auth.schemas import (
    TokenRefreshRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from backend.app.modules.auth.service import auth_service
from backend.app.schemas.common import ResponseEnvelope

router = APIRouter(tags=["Authentication"])


@router.post(
    "/register",
    response_model=ResponseEnvelope[UserResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(
    payload: UserRegisterRequest,
    session: AsyncSession = Depends(get_db_session),
):
    """Creates a new user account with hashed credentials."""
    user = await auth_service.register_user(session, payload)
    await session.commit()
    return ResponseEnvelope(
        data=UserResponse.model_validate(user),
        message="User registered successfully",
    )


@router.post(
    "/login",
    response_model=ResponseEnvelope[TokenResponse],
    summary="Authenticate user and obtain JWT tokens",
)
async def login(
    payload: UserLoginRequest,
    session: AsyncSession = Depends(get_db_session),
):
    """Authenticates credentials and returns an access/refresh token pair."""
    user = await auth_service.authenticate_user(session, payload)
    token_resp = auth_service.generate_token_response(user)
    return ResponseEnvelope(
        data=token_resp,
        message="Authentication successful",
    )


@router.post(
    "/refresh",
    response_model=ResponseEnvelope[TokenResponse],
    summary="Refresh an expired access token using a refresh token",
)
async def refresh_token(
    payload: TokenRefreshRequest,
    session: AsyncSession = Depends(get_db_session),
):
    """Exchanges a valid refresh token for a fresh token pair."""
    token_resp = await auth_service.refresh_tokens(session, payload.refresh_token)
    return ResponseEnvelope(
        data=token_resp,
        message="Token refreshed successfully",
    )


@router.get(
    "/me",
    response_model=ResponseEnvelope[UserResponse],
    summary="Retrieve current user profile",
)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    """Returns the profile of the currently authenticated user."""
    return ResponseEnvelope(
        data=UserResponse.model_validate(current_user),
    )
