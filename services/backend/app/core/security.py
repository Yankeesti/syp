"""Security utilities for JWT token management.

This module provides functions for creating and verifying JWT tokens
used for authentication after successful Magic Link verification.
"""

from datetime import datetime, timedelta, timezone

from jose import jwt, JWTError

from app.core.config import get_settings
from app.shared.schemas import TokenPayload


def create_jwt_token(payload: TokenPayload) -> str:
    """
    Generate a JWT token for authenticated user.

    Args:
        payload: TokenPayload containing user data to encode

    Returns:
        Encoded JWT token string

    Notes:
        - Token expires after JWT_EXPIRATION_HOURS (default: 5 hours)
        - Payload is serialized via TokenPayload.to_jwt_claims()
        - Signed with JWT_SECRET_KEY using HMAC-SHA256
    """
    settings = get_settings()

    expiration = datetime.now(timezone.utc) + timedelta(
        hours=settings.jwt_expiration_hours,
    )

    claims = payload.to_jwt_claims()
    claims["exp"] = expiration

    token = jwt.encode(
        claims,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    return token


def verify_jwt_token(token: str) -> TokenPayload:
    """
    Verify and decode a JWT token.

    Args:
        token: The JWT token string to verify

    Returns:
        TokenPayload containing authenticated user data

    Raises:
        JWTError: If token is invalid, expired, or malformed
        KeyError: If required claims are missing
        ValueError: If claim values are invalid
    """
    settings = get_settings()

    claims = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )

    return TokenPayload.from_jwt_claims(claims)
