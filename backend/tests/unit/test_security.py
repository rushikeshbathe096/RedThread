import uuid
from datetime import timedelta
import pytest
import jwt

from backend.app.core.config import settings
from backend.app.core.exceptions import AuthenticationError
from backend.app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)


def test_password_hashing_and_verification():
    password = "SuperSecretPassword123!"
    hashed = get_password_hash(password)

    # Must be Argon2id format
    assert hashed.startswith("$argon2id$")
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_password_verification_edge_cases():
    assert verify_password("", "somehash") is False
    assert verify_password("password", "") is False
    assert verify_password("password", "invalid_format_hash") is False

    with pytest.raises(ValueError):
        get_password_hash("")


def test_access_token_creation_and_decoding():
    user_id = uuid.uuid4()
    org_id = uuid.uuid4()
    role = "lead_investigator"

    token = create_access_token(subject=user_id, org_id=org_id, role=role)
    payload = decode_token(token, expected_type="access")

    assert payload["sub"] == str(user_id)
    assert payload["org_id"] == str(org_id)
    assert payload["role"] == role
    assert payload["type"] == "access"
    assert "jti" in payload
    assert "exp" in payload
    assert "iat" in payload


def test_refresh_token_creation_and_decoding():
    user_id = uuid.uuid4()

    token = create_refresh_token(subject=user_id)
    payload = decode_token(token, expected_type="refresh")

    assert payload["sub"] == str(user_id)
    assert payload["type"] == "refresh"
    assert "jti" in payload


def test_token_type_mismatch_raises_authentication_error():
    user_id = uuid.uuid4()
    refresh_token = create_refresh_token(subject=user_id)

    # Calling decode_token expecting 'access' on a 'refresh' token must fail
    with pytest.raises(AuthenticationError) as exc_info:
        decode_token(refresh_token, expected_type="access")
    assert "Invalid token type" in str(exc_info.value.message)


def test_expired_token_raises_authentication_error():
    user_id = uuid.uuid4()
    # Expired 10 minutes ago
    expired_token = create_access_token(
        subject=user_id, expires_delta=timedelta(minutes=-10)
    )

    with pytest.raises(AuthenticationError) as exc_info:
        decode_token(expired_token)
    assert "Token has expired" in str(exc_info.value.message)


def test_tampered_token_raises_authentication_error():
    user_id = uuid.uuid4()
    token = create_access_token(subject=user_id)

    # Sign with a different key
    tampered = jwt.encode(
        {"sub": str(user_id), "type": "access"},
        "wrong-secret-key-32bytes-long-padding-ok",
        algorithm="HS256",
    )

    with pytest.raises(AuthenticationError) as exc_info:
        decode_token(tampered)
    assert "Invalid authentication token" in str(exc_info.value.message)
