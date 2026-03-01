"""Unit tests for MagicLinkService."""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest

from app.modules.auth.models import MagicLinkToken, User
from app.modules.auth.exceptions import (
    MagicLinkTokenExpiredError,
    MagicLinkTokenInvalidError,
    UserNotRegisteredError,
)
from app.modules.auth.services.dtos import MagicLinkResult, TokenResult
from app.modules.auth.services import MagicLinkService
from app.shared.schemas import TokenPayload


pytestmark = pytest.mark.unit


class TestMagicLinkServiceHashFunction:
    """Test suite for the _hash static method."""

    def test_hash_deterministic(self):
        """Test that hashing the same input produces the same output."""
        # Arrange
        input_data = "test@example.com"

        # Act
        hash1 = MagicLinkService._hash(input_data)
        hash2 = MagicLinkService._hash(input_data)

        # Assert
        assert hash1 == hash2

    def test_hash_different_inputs(self):
        """Test that different inputs produce different hashes."""
        # Arrange
        input1 = "test1@example.com"
        input2 = "test2@example.com"

        # Act
        hash1 = MagicLinkService._hash(input1)
        hash2 = MagicLinkService._hash(input2)

        # Assert
        assert hash1 != hash2

    def test_hash_length(self):
        """Test that hash is 64 characters (SHA-256 in hex)."""
        # Arrange
        input_data = "test@example.com"

        # Act
        result = MagicLinkService._hash(input_data)

        # Assert
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)


class TestMagicLinkServiceRequestMagicLink:
    """Test suite for request_magic_link method."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        db = AsyncMock()
        db.commit = AsyncMock()
        return db

    @pytest.fixture
    def mock_token_repo(self):
        """Mock MagicLinkTokenRepository."""
        repo = AsyncMock()
        repo.create = AsyncMock()
        return repo

    @pytest.fixture
    def mock_user_repo(self):
        """Mock UserRepository."""
        repo = AsyncMock()
        repo.get_by_email_hash = AsyncMock(return_value=None)
        repo.create = AsyncMock()
        return repo

    @pytest.fixture
    def existing_user(self):
        """Create an existing user."""
        return User(
            user_id=uuid.uuid4(),
            email_hash=MagicLinkService._hash("test@example.com"),
            created_at=datetime.now(timezone.utc),
        )

    @pytest.fixture
    def service(self, mock_db, mock_token_repo, mock_user_repo, existing_user):
        """Create service with mocked dependencies."""
        mock_user_repo.get_by_email_hash.return_value = existing_user
        service = MagicLinkService(
            db=mock_db,
            user_repo=mock_user_repo,
            token_repo=mock_token_repo,
        )
        service.send_magic_link = AsyncMock()
        return service

    async def test_request_magic_link_success(self, service, mock_db):
        """Test successful magic link request."""
        # Arrange
        email = "test@example.com"

        # Act
        response = await service.request_magic_link(email)

        # Assert
        assert isinstance(response, MagicLinkResult)
        assert response.expires_in == 300  # 5 minutes in seconds
        mock_db.commit.assert_called_once()

    async def test_request_magic_link_missing_user_raises(
        self,
        service,
        mock_db,
        mock_user_repo,
        mock_token_repo,
    ):
        """Test that missing users get a generic response."""
        # Arrange
        email = "missing@example.com"
        mock_user_repo.get_by_email_hash.return_value = None

        # Act & Assert
        response = await service.request_magic_link(email)

        assert isinstance(response, MagicLinkResult)
        assert response.expires_in == 300
        mock_db.commit.assert_not_called()
        mock_token_repo.create.assert_not_called()
        service.send_magic_link.assert_not_called()

    async def test_register_user_and_request_magic_link_success(
        self,
        service,
        mock_user_repo,
    ):
        """Test registration creates a user and sends a magic link."""
        # Arrange
        email = "new-user@example.com"
        mock_user_repo.get_by_email_hash.return_value = None

        # Act
        response = await service.register_user_and_request_magic_link(email)

        # Assert
        assert isinstance(response, MagicLinkResult)
        assert response.expires_in == 300
        assert response.already_registered is False
        mock_user_repo.create.assert_called_once_with(
            email_hash=MagicLinkService._hash(email),
        )

    async def test_register_user_and_request_magic_link_existing_user_raises(
        self,
        service,
        mock_user_repo,
        existing_user,
    ):
        """Test registration returns generic response for existing user."""
        # Arrange
        email = "test@example.com"
        mock_user_repo.get_by_email_hash.return_value = existing_user

        # Act & Assert
        response = await service.register_user_and_request_magic_link(email)

        assert isinstance(response, MagicLinkResult)
        assert response.expires_in == 300
        assert response.already_registered is True
        mock_user_repo.create.assert_not_called()

    async def test_request_magic_link_creates_token_hash(
        self,
        service,
        mock_token_repo,
    ):
        """Test that token_hash is created and stored."""
        # Arrange
        email = "test@example.com"

        # Act
        await service.request_magic_link(email)

        # Assert
        mock_token_repo.create.assert_called_once()
        call_kwargs = mock_token_repo.create.call_args.kwargs
        assert "token_hash" in call_kwargs
        assert len(call_kwargs["token_hash"]) == 64  # SHA-256 hex

    async def test_request_magic_link_creates_email_hash(
        self,
        service,
        mock_token_repo,
    ):
        """Test that email_hash is created correctly."""
        # Arrange
        email = "test@example.com"
        expected_email_hash = MagicLinkService._hash(email)

        # Act
        await service.request_magic_link(email)

        # Assert
        call_kwargs = mock_token_repo.create.call_args.kwargs
        assert call_kwargs["email_hash"] == expected_email_hash

    @patch("app.modules.auth.services.magic_link_service.datetime")
    async def test_request_magic_link_sets_expiration(
        self,
        mock_datetime,
        service,
        mock_token_repo,
    ):
        """Test that expiration is set to 5 minutes in the future."""
        # Arrange
        email = "test@example.com"
        now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = now

        # Act
        await service.request_magic_link(email)

        # Assert
        call_kwargs = mock_token_repo.create.call_args.kwargs
        expected_expiration = now + timedelta(minutes=5)
        assert call_kwargs["expires_at"] == expected_expiration

    async def test_request_magic_link_commits_transaction(self, service, mock_db):
        """Test that db.commit() is called."""
        # Arrange
        email = "test@example.com"

        # Act
        await service.request_magic_link(email)

        # Assert
        mock_db.commit.assert_called_once()

    async def test_request_magic_link_returns_correct_response(self, service):
        """Test that the response structure is correct."""
        # Arrange
        email = "test@example.com"

        # Act
        response = await service.request_magic_link(email)

        # Assert
        assert isinstance(response, MagicLinkResult)
        assert hasattr(response, "expires_in")
        assert isinstance(response.expires_in, int)
        assert isinstance(response.expires_in, int)


class TestMagicLinkServiceVerifyMagicLink:
    """Test suite for verify_magic_link method."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        db = AsyncMock()
        db.commit = AsyncMock()
        return db

    @pytest.fixture
    def mock_token_repo(self):
        """Mock MagicLinkTokenRepository."""
        repo = AsyncMock()
        repo.get_by_token_hash = AsyncMock()
        repo.delete = AsyncMock()
        return repo

    @pytest.fixture
    def mock_user_repo(self):
        """Mock UserRepository."""
        repo = AsyncMock()
        repo.get_by_email_hash = AsyncMock()
        repo.create = AsyncMock()
        return repo

    @pytest.fixture
    def service(self, mock_db, mock_token_repo, mock_user_repo):
        """Create service with mocked dependencies."""
        return MagicLinkService(
            db=mock_db,
            user_repo=mock_user_repo,
            token_repo=mock_token_repo,
        )

    @pytest.fixture
    def valid_token(self):
        """Create a valid magic link token."""
        return MagicLinkToken(
            id=uuid.uuid4(),
            token_hash="valid_token_hash",
            email_hash="email_hash_123",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
            created_at=datetime.now(timezone.utc),
        )

    @pytest.fixture
    def existing_user(self):
        """Create an existing user."""
        return User(
            user_id=uuid.uuid4(),
            email_hash="email_hash_123",
            created_at=datetime.now(timezone.utc),
        )

    @patch("app.modules.auth.services.magic_link_service.create_jwt_token")
    async def test_verify_valid_token_existing_user(
        self,
        mock_create_jwt,
        service,
        mock_token_repo,
        mock_user_repo,
        valid_token,
        existing_user,
    ):
        """Test verification with valid token and existing user (login)."""
        # Arrange
        token_string = "valid_token"
        mock_token_repo.get_by_token_hash.return_value = valid_token
        mock_user_repo.get_by_email_hash.return_value = existing_user
        mock_create_jwt.return_value = "jwt_token_123"

        # Act
        response = await service.verify_magic_link(token_string)

        # Assert
        assert isinstance(response, TokenResult)
        assert response.access_token == "jwt_token_123"
        assert response.token_type == "bearer"
        mock_token_repo.delete.assert_called_once_with(valid_token.id)
        mock_user_repo.create.assert_not_called()  # User already exists

    async def test_verify_valid_token_missing_user_raises(
        self,
        service,
        mock_db,
        mock_token_repo,
        mock_user_repo,
        valid_token,
    ):
        """Test verification fails when user does not exist."""
        # Arrange
        token_string = "valid_token"
        mock_token_repo.get_by_token_hash.return_value = valid_token
        mock_user_repo.get_by_email_hash.return_value = None

        # Act & Assert
        with pytest.raises(UserNotRegisteredError):
            await service.verify_magic_link(token_string)
        mock_token_repo.delete.assert_called_once_with(valid_token.id)
        mock_user_repo.create.assert_not_called()
        mock_db.commit.assert_called_once()

    @patch("app.modules.auth.services.magic_link_service.create_jwt_token")
    async def test_verify_returns_jwt_token(
        self,
        mock_create_jwt,
        service,
        mock_token_repo,
        mock_user_repo,
        valid_token,
        existing_user,
    ):
        """Test that JWT token is generated and returned."""
        # Arrange
        token_string = "valid_token"
        mock_token_repo.get_by_token_hash.return_value = valid_token
        mock_user_repo.get_by_email_hash.return_value = existing_user
        mock_create_jwt.return_value = "generated_jwt_token"

        # Act
        response = await service.verify_magic_link(token_string)

        # Assert
        mock_create_jwt.assert_called_once()
        call_arg = mock_create_jwt.call_args[0][0]
        assert isinstance(call_arg, TokenPayload)
        assert call_arg.user_id == existing_user.user_id
        assert response.access_token == "generated_jwt_token"

    @patch("app.modules.auth.services.magic_link_service.create_jwt_token")
    async def test_verify_returns_token_response(
        self,
        mock_create_jwt,
        service,
        mock_token_repo,
        mock_user_repo,
        valid_token,
        existing_user,
    ):
        """Test that TokenResult is returned with correct structure."""
        # Arrange
        token_string = "valid_token"
        mock_token_repo.get_by_token_hash.return_value = valid_token
        mock_user_repo.get_by_email_hash.return_value = existing_user
        mock_create_jwt.return_value = "jwt_token"

        # Act
        response = await service.verify_magic_link(token_string)

        # Assert
        assert hasattr(response, "access_token")
        assert hasattr(response, "token_type")
        assert response.token_type == "bearer"

    async def test_verify_token_not_found(self, service, mock_token_repo):
        """Test that MagicLinkTokenInvalidError is raised when token not found."""
        # Arrange
        token_string = "invalid_token"
        mock_token_repo.get_by_token_hash.return_value = None

        # Act & Assert
        with pytest.raises(MagicLinkTokenInvalidError):
            await service.verify_magic_link(token_string)

    async def test_verify_token_expired(self, service, mock_token_repo, mock_db):
        """Test that MagicLinkTokenExpiredError is raised when token is expired."""
        # Arrange
        token_string = "expired_token"
        expired_token = MagicLinkToken(
            id=uuid.uuid4(),
            token_hash="expired_token_hash",
            email_hash="email_hash",
            expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),  # Expired
            created_at=datetime.now(timezone.utc) - timedelta(minutes=6),
        )
        mock_token_repo.get_by_token_hash.return_value = expired_token

        # Act & Assert
        with pytest.raises(MagicLinkTokenExpiredError):
            await service.verify_magic_link(token_string)
        mock_token_repo.delete.assert_called_once_with(expired_token.id)

    async def test_verify_expired_token_gets_deleted(
        self,
        service,
        mock_token_repo,
        mock_db,
    ):
        """Test that expired tokens are deleted from database."""
        # Arrange
        token_string = "expired_token"
        expired_token = MagicLinkToken(
            id=uuid.uuid4(),
            token_hash="expired_token_hash",
            email_hash="email_hash",
            expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
            created_at=datetime.now(timezone.utc) - timedelta(minutes=6),
        )
        mock_token_repo.get_by_token_hash.return_value = expired_token

        # Act & Assert
        with pytest.raises(MagicLinkTokenExpiredError):
            await service.verify_magic_link(token_string)

        mock_token_repo.delete.assert_called_once_with(expired_token.id)
        mock_db.commit.assert_called_once()

    @patch("app.modules.auth.services.magic_link_service.create_jwt_token")
    async def test_verify_deletes_token_after_use(
        self,
        mock_create_jwt,
        service,
        mock_token_repo,
        mock_user_repo,
        valid_token,
        existing_user,
    ):
        """Test that token is deleted after successful verification (single-use)."""
        # Arrange
        token_string = "valid_token"
        mock_token_repo.get_by_token_hash.return_value = valid_token
        mock_user_repo.get_by_email_hash.return_value = existing_user
        mock_create_jwt.return_value = "jwt_token"

        # Act
        await service.verify_magic_link(token_string)

        # Assert
        mock_token_repo.delete.assert_called_once_with(valid_token.id)

    @patch("app.modules.auth.services.magic_link_service.create_jwt_token")
    async def test_verify_commits_transaction(
        self,
        mock_create_jwt,
        service,
        mock_db,
        mock_token_repo,
        mock_user_repo,
        valid_token,
        existing_user,
    ):
        """Test that db.commit() is called."""
        # Arrange
        token_string = "valid_token"
        mock_token_repo.get_by_token_hash.return_value = valid_token
        mock_user_repo.get_by_email_hash.return_value = existing_user
        mock_create_jwt.return_value = "jwt_token"

        # Act
        await service.verify_magic_link(token_string)

        # Assert
        mock_db.commit.assert_called_once()
