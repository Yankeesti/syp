"""Unit tests for security module (JWT token functions)."""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from freezegun import freeze_time
from jose import JWTError, jwt

from app.core.security import create_jwt_token, verify_jwt_token
from app.shared.schemas import TokenPayload


pytestmark = pytest.mark.unit


class TestCreateJwtToken:
    """Test suite for create_jwt_token function."""

    def test_create_jwt_token_contains_user_id(self):
        """Test that the JWT payload contains user_id."""
        # Arrange
        from app.core.config import get_settings

        settings = get_settings()
        user_id = uuid.uuid4()
        payload = TokenPayload(user_id=user_id)

        # Act
        token = create_jwt_token(payload)
        decoded = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        # Assert
        assert "user_id" in decoded
        assert decoded["user_id"] == str(user_id)

    def test_create_jwt_token_contains_expiration(self):
        """Test that the JWT payload contains exp (expiration)."""
        # Arrange
        from app.core.config import get_settings

        settings = get_settings()
        user_id = uuid.uuid4()
        payload = TokenPayload(user_id=user_id)

        # Act
        token = create_jwt_token(payload)
        decoded = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        # Assert
        assert "exp" in decoded
        assert isinstance(decoded["exp"], (int, float))

    @freeze_time("2024-01-01 12:00:00", tz_offset=0)
    def test_create_jwt_token_expiration_is_5_hours(self):
        """Test that token expires after 5 hours."""
        # Arrange
        from app.core.config import get_settings

        settings = get_settings()
        user_id = uuid.uuid4()
        payload = TokenPayload(user_id=user_id)
        now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        expected_exp = now + timedelta(hours=5)

        # Act
        token = create_jwt_token(payload)
        decoded = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        # Assert
        assert decoded["exp"] == int(expected_exp.timestamp())

    def test_create_jwt_token_is_string(self):
        """Test that the token is a string."""
        # Arrange
        user_id = uuid.uuid4()
        payload = TokenPayload(user_id=user_id)

        # Act
        token = create_jwt_token(payload)

        # Assert
        assert isinstance(token, str)

    def test_create_jwt_token_format(self):
        """Test that token has JWT format (3 parts separated by dots)."""
        # Arrange
        user_id = uuid.uuid4()
        payload = TokenPayload(user_id=user_id)

        # Act
        token = create_jwt_token(payload)

        # Assert
        parts = token.split(".")
        assert len(parts) == 3  # header.payload.signature


class TestVerifyJwtToken:
    """Test suite for verify_jwt_token function."""

    def test_verify_valid_token(self):
        """Test that a valid token is correctly decoded."""
        # Arrange
        user_id = uuid.uuid4()
        payload = TokenPayload(user_id=user_id)
        token = create_jwt_token(payload)

        # Act
        result = verify_jwt_token(token)

        # Assert
        assert result is not None
        assert isinstance(result, TokenPayload)

    def test_verify_returns_user_id(self):
        """Test that user_id from payload is returned."""
        # Arrange
        user_id = uuid.uuid4()
        payload = TokenPayload(user_id=user_id)
        token = create_jwt_token(payload)

        # Act
        result = verify_jwt_token(token)

        # Assert
        assert result.user_id == user_id

    def test_verify_expired_token_raises_error(self):
        """Test that JWTError is raised for expired token."""
        # Arrange
        user_id = uuid.uuid4()
        payload = TokenPayload(user_id=user_id)

        # Create token that's already expired
        with freeze_time("2024-01-01 12:00:00", tz_offset=0):
            token = create_jwt_token(payload)

        # Act & Assert (6 hours later - token should be expired)
        with freeze_time("2024-01-01 18:01:00", tz_offset=0):
            with pytest.raises(JWTError):
                verify_jwt_token(token)

    def test_verify_invalid_signature_raises_error(self):
        """Test that JWTError is raised when signature is invalid."""
        # Arrange
        user_id = uuid.uuid4()
        payload = TokenPayload(user_id=user_id)
        token = create_jwt_token(payload)

        # Tamper with the token by changing the second-to-last character.
        # The last character is unreliable: its lowest 2 bits are base64url
        # padding that gets ignored on decode, so some replacements leave the
        # signature unchanged.
        tampered_token = token[:-2] + ("X" if token[-2] != "X" else "Y") + token[-1]

        # Act & Assert
        with pytest.raises(JWTError):
            verify_jwt_token(tampered_token)

    def test_verify_malformed_token_raises_error(self):
        """Test that JWTError is raised for malformed token."""
        # Arrange
        malformed_token = "this.is.not.a.valid.jwt"

        # Act & Assert
        with pytest.raises(JWTError):
            verify_jwt_token(malformed_token)

    def test_verify_empty_token_raises_error(self):
        """Test that JWTError is raised for empty token."""
        # Arrange
        empty_token = ""

        # Act & Assert
        with pytest.raises(JWTError):
            verify_jwt_token(empty_token)

    def test_verify_token_with_wrong_algorithm(self):
        """Test that JWTError is raised when token uses wrong algorithm."""
        # Arrange
        from app.core.config import get_settings

        settings = get_settings()
        user_id = uuid.uuid4()

        # Create token with different algorithm (HS512 instead of HS256)
        claims = {
            "user_id": str(user_id),
            "exp": datetime.now(timezone.utc) + timedelta(hours=5),
        }
        wrong_algo_token = jwt.encode(
            claims,
            settings.jwt_secret_key,
            algorithm="HS512",
        )

        # Act & Assert
        with pytest.raises(JWTError):
            verify_jwt_token(wrong_algo_token)

    def test_verify_token_missing_user_id_raises_error(self):
        """Test that KeyError is raised when user_id is missing from payload."""
        # Arrange
        from app.core.config import get_settings

        settings = get_settings()

        # Create token without user_id
        claims = {"exp": datetime.now(timezone.utc) + timedelta(hours=5)}
        token = jwt.encode(
            claims,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )

        # Act & Assert
        with pytest.raises(KeyError):
            verify_jwt_token(token)

    @freeze_time("2024-01-01 12:00:00", tz_offset=0)
    def test_verify_token_just_before_expiry(self):
        """Test that token is valid just before expiration."""
        # Arrange
        user_id = uuid.uuid4()
        payload = TokenPayload(user_id=user_id)
        token = create_jwt_token(payload)

        # Act - Almost 5 hours later (4:59:59)
        with freeze_time("2024-01-01 16:59:59", tz_offset=0):
            result = verify_jwt_token(token)

        # Assert
        assert result.user_id == user_id
