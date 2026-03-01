"""Unit tests for MagicLinkTokenRepository."""

import uuid
from datetime import datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from app.modules.auth.models import MagicLinkToken
from app.modules.auth.repositories.magic_link_token_repository import (
    MagicLinkTokenRepository,
)


pytestmark = pytest.mark.unit


class TestMagicLinkTokenRepository:
    """Test suite for MagicLinkTokenRepository."""

    @pytest.fixture
    def repository(self, db_session):
        """Create a repository instance for testing."""
        return MagicLinkTokenRepository(db_session)

    async def test_create_token_success(self, repository, db_session):
        """Test successful creation of a magic link token."""
        # Arrange
        token_hash = "abc123hash"
        email_hash = "xyz789hash"
        expires_at = datetime.now() + timedelta(minutes=5)

        # Act
        token = await repository.create(
            token_hash=token_hash,
            email_hash=email_hash,
            expires_at=expires_at,
        )
        await db_session.commit()

        # Assert
        assert token is not None
        assert isinstance(token.id, uuid.UUID)
        assert token.token_hash == token_hash
        assert token.email_hash == email_hash
        assert token.expires_at == expires_at
        assert isinstance(token.created_at, datetime)

    async def test_create_token_duplicate_token_hash(self, repository, db_session):
        """Test that creating a token with duplicate token_hash raises IntegrityError."""
        # Arrange
        token_hash = "duplicate_hash"
        email_hash_1 = "email1_hash"
        email_hash_2 = "email2_hash"
        expires_at = datetime.now() + timedelta(minutes=5)

        # Create first token
        await repository.create(
            token_hash=token_hash,
            email_hash=email_hash_1,
            expires_at=expires_at,
        )
        await db_session.commit()

        # Act & Assert
        with pytest.raises(IntegrityError):
            await repository.create(
                token_hash=token_hash,  # Same token_hash
                email_hash=email_hash_2,
                expires_at=expires_at,
            )
            await db_session.commit()

    async def test_get_by_token_hash_exists(self, repository, db_session):
        """Test retrieving a token by token_hash when it exists."""
        # Arrange
        token_hash = "find_me_hash"
        email_hash = "email_hash"
        expires_at = datetime.now() + timedelta(minutes=5)

        created_token = await repository.create(
            token_hash=token_hash,
            email_hash=email_hash,
            expires_at=expires_at,
        )
        await db_session.commit()

        # Act
        found_token = await repository.get_by_token_hash(token_hash)

        # Assert
        assert found_token is not None
        assert found_token.id == created_token.id
        assert found_token.token_hash == token_hash
        assert found_token.email_hash == email_hash

    async def test_get_by_token_hash_not_found(self, repository):
        """Test that get_by_token_hash returns None when token doesn't exist."""
        # Act
        found_token = await repository.get_by_token_hash("nonexistent_hash")

        # Assert
        assert found_token is None

    async def test_delete_token_success(self, repository, db_session):
        """Test successful deletion of a token."""
        # Arrange
        token_hash = "delete_me_hash"
        email_hash = "email_hash"
        expires_at = datetime.now() + timedelta(minutes=5)

        created_token = await repository.create(
            token_hash=token_hash,
            email_hash=email_hash,
            expires_at=expires_at,
        )
        await db_session.commit()

        # Act
        result = await repository.delete(created_token.id)
        await db_session.commit()

        # Assert
        assert result is True

        # Verify token is actually deleted
        found_token = await repository.get_by_token_hash(token_hash)
        assert found_token is None

    async def test_delete_token_not_found(self, repository):
        """Test that deleting a non-existent token returns False."""
        # Arrange
        nonexistent_id = uuid.uuid4()

        # Act
        result = await repository.delete(nonexistent_id)

        # Assert
        assert result is False
