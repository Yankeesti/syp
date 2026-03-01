"""Unit tests for shared dependencies (authentication)."""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from jose import JWTError

from app.core.security import create_jwt_token
from app.shared.dependencies import get_current_user, get_current_user_id
from app.shared.schemas import TokenPayload


pytestmark = pytest.mark.unit


class TestGetCurrentUser:
    """Test suite for get_current_user dependency."""

    async def test_valid_token_returns_token_payload(self):
        """Test that valid token returns TokenPayload."""
        # Arrange
        user_id = uuid.uuid4()
        payload = TokenPayload(user_id=user_id)
        token = create_jwt_token(payload)
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token,
        )

        # Act
        result = await get_current_user(credentials)

        # Assert
        assert isinstance(result, TokenPayload)
        assert result.user_id == user_id

    async def test_invalid_token_raises_401(self):
        """Test that invalid token raises HTTPException 401."""
        # Arrange
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid.token.here",
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid or expired token"
        assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}

    async def test_expired_token_raises_401(self):
        """Test that expired token raises HTTPException 401."""
        from freezegun import freeze_time

        # Arrange - Create token in the past
        user_id = uuid.uuid4()
        payload = TokenPayload(user_id=user_id)

        with freeze_time("2024-01-01 12:00:00", tz_offset=0):
            token = create_jwt_token(payload)

        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token,
        )

        # Act & Assert - Verify 6 hours later (token expires after 5h)
        with freeze_time("2024-01-01 18:01:00", tz_offset=0):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(credentials)

        assert exc_info.value.status_code == 401

    async def test_token_missing_user_id_raises_401(self):
        """Test that token without user_id raises HTTPException 401."""
        from datetime import datetime, timedelta, timezone

        from jose import jwt

        from app.core.config import get_settings

        # Arrange - Create token without user_id
        settings = get_settings()
        claims = {"exp": datetime.now(timezone.utc) + timedelta(hours=5)}
        token = jwt.encode(
            claims,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token,
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials)

        assert exc_info.value.status_code == 401

    async def test_token_invalid_uuid_raises_401(self):
        """Test that token with invalid UUID format raises HTTPException 401."""
        from datetime import datetime, timedelta, timezone

        from jose import jwt

        from app.core.config import get_settings

        # Arrange - Create token with invalid user_id
        settings = get_settings()
        claims = {
            "user_id": "not-a-valid-uuid",
            "exp": datetime.now(timezone.utc) + timedelta(hours=5),
        }
        token = jwt.encode(
            claims,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token,
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials)

        assert exc_info.value.status_code == 401

    async def test_empty_token_raises_401(self):
        """Test that empty token raises HTTPException 401."""
        # Arrange
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="",
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials)

        assert exc_info.value.status_code == 401


class TestGetCurrentUserId:
    """Test suite for get_current_user_id dependency."""

    async def test_returns_user_id_from_token_payload(self):
        """Test that user_id is extracted from TokenPayload."""
        # Arrange
        user_id = uuid.uuid4()
        payload = TokenPayload(user_id=user_id)

        # Act
        result = await get_current_user_id(payload)

        # Assert
        assert result == user_id
        assert isinstance(result, uuid.UUID)

    async def test_returns_uuid_type(self):
        """Test that return type is UUID."""
        # Arrange
        user_id = uuid.uuid4()
        payload = TokenPayload(user_id=user_id)

        # Act
        result = await get_current_user_id(payload)

        # Assert
        assert type(result) is uuid.UUID
