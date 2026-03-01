"""Shared dependencies for FastAPI routes."""

import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.security import verify_jwt_token
from app.shared.schemas import TokenPayload
from app.core.email import MailService

# Database session dependency
DBSessionDep = Annotated[AsyncSession, Depends(get_db_session)]

# HTTP Bearer security scheme for Swagger UI integration
http_bearer = HTTPBearer()

# Mail service dependency
_mailer = None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
) -> TokenPayload:
    """
    Extract and validate token payload from JWT Bearer token.

    Args:
        credentials: HTTP Bearer credentials extracted by FastAPI

    Returns:
        TokenPayload containing authenticated user data

    Raises:
        HTTPException: 401 Unauthorized if token is invalid or expired
    """
    try:
        return verify_jwt_token(credentials.credentials)
    except (JWTError, KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_id(
    user: TokenPayload = Depends(get_current_user),
) -> uuid.UUID:
    """
    Convenience dependency that returns only the user ID.

    Args:
        user: TokenPayload from get_current_user dependency

    Returns:
        UUID of the authenticated user
    """
    return user.user_id


async def get_mailer():
    global _mailer
    if _mailer is None:
        _mailer = MailService()
    return _mailer


# Type aliases for dependency injection
CurrentUser = Annotated[TokenPayload, Depends(get_current_user)]
CurrentUserId = Annotated[uuid.UUID, Depends(get_current_user_id)]
