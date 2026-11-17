import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union

import argon2
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
import jwt

from backend.app.core.config import settings
from backend.app.core.exceptions import AuthenticationError

# Instantiate Argon2id Password Hasher with parameters specified in configuration
_pwd_hasher = argon2.PasswordHasher(
    time_cost=settings.ARGON2_TIME_COST,
    memory_cost=settings.ARGON2_MEMORY_COST,
    parallelism=settings.ARGON2_PARALLELISM,
    hash_len=32,
    type=argon2.Type.ID,
)


def get_password_hash(password: str) -> str:
    """Hashes a plaintext password using Argon2id with memory-hardness and side-channel resistance."""
    if not password:
        raise ValueError("Password cannot be empty")
    return _pwd_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against an Argon2id hash. Returns True on match, False otherwise."""
    if not plain_password or not hashed_password:
        return False
    try:
        return _pwd_hasher.verify(hashed_password, plain_password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def create_access_token(
    subject: Union[str, uuid.UUID],
    org_id: Optional[Union[str, uuid.UUID]] = None,
    role: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Creates a signed, short-lived JWT access token containing identity and tenant context claims."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: Dict[str, Any] = {
        "sub": str(subject),
        "type": "access",
        "jti": str(uuid.uuid4()),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    if org_id is not None:
        payload["org_id"] = str(org_id)
    if role is not None:
        payload["role"] = str(role)

    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(
    subject: Union[str, uuid.UUID],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Creates a signed, long-lived JWT refresh token used strictly for rotating token renewal."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    payload: Dict[str, Any] = {
        "sub": str(subject),
        "type": "refresh",
        "jti": str(uuid.uuid4()),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str, expected_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Decodes and cryptographically verifies a JWT token.
    Enforces algorithm pinning, expiration checks, and optional token type validation.
    Raises AuthenticationError on invalid signatures, expired tokens, or mismatched types.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token has expired")
    except jwt.InvalidTokenError:
        raise AuthenticationError("Invalid authentication token")

    if expected_type is not None:
        token_type = payload.get("type")
        if token_type != expected_type:
            raise AuthenticationError(
                f"Invalid token type: expected '{expected_type}', got '{token_type}'"
            )

    return payload
