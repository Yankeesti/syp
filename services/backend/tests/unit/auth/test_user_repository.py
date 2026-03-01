"""Unit tests for UserRepository."""

import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app.modules.auth.models import User
from app.modules.auth.repositories.user_repository import UserRepository


pytestmark = pytest.mark.unit


class TestUserRepository:
    """Test suite for UserRepository."""

    @pytest.fixture
    def repository(self, db_session):
        """Create a repository instance for testing."""
        return UserRepository(db_session)

    async def test_create_user_success(self, repository, db_session):
        """Test successful creation of a user."""
        # Arrange
        email_hash = "user_email_hash_123"

        # Act
        user = await repository.create(email_hash=email_hash)
        await db_session.commit()

        # Assert
        assert user is not None
        assert isinstance(user.user_id, uuid.UUID)
        assert user.email_hash == email_hash
        assert user.created_at is not None

    async def test_create_user_duplicate_email_hash(self, repository, db_session):
        """Test that creating a user with duplicate email_hash raises IntegrityError."""
        # Arrange
        email_hash = "duplicate_email_hash"

        # Create first user
        await repository.create(email_hash=email_hash)
        await db_session.commit()

        # Act & Assert
        with pytest.raises(IntegrityError):
            await repository.create(email_hash=email_hash)
            await db_session.commit()

    async def test_get_by_id_exists(self, repository, db_session):
        """Test retrieving a user by ID when it exists."""
        # Arrange
        email_hash = "test_email_hash"
        created_user = await repository.create(email_hash=email_hash)
        await db_session.commit()

        # Act
        found_user = await repository.get_by_id(created_user.user_id)

        # Assert
        assert found_user is not None
        assert found_user.user_id == created_user.user_id
        assert found_user.email_hash == email_hash

    async def test_get_by_id_not_found(self, repository):
        """Test that get_by_id returns None when user doesn't exist."""
        # Arrange
        nonexistent_id = uuid.uuid4()

        # Act
        found_user = await repository.get_by_id(nonexistent_id)

        # Assert
        assert found_user is None

    async def test_get_by_email_hash_exists(self, repository, db_session):
        """Test retrieving a user by email_hash when it exists."""
        # Arrange
        email_hash = "find_by_email_hash"
        created_user = await repository.create(email_hash=email_hash)
        await db_session.commit()

        # Act
        found_user = await repository.get_by_email_hash(email_hash)

        # Assert
        assert found_user is not None
        assert found_user.user_id == created_user.user_id
        assert found_user.email_hash == email_hash

    async def test_get_by_email_hash_not_found(self, repository):
        """Test that get_by_email_hash returns None when user doesn't exist."""
        # Act
        found_user = await repository.get_by_email_hash("nonexistent_email_hash")

        # Assert
        assert found_user is None

    async def test_exists_by_email_hash_true(self, repository, db_session):
        """Test that exists_by_email_hash returns True when user exists."""
        # Arrange
        email_hash = "existing_user_hash"
        await repository.create(email_hash=email_hash)
        await db_session.commit()

        # Act
        exists = await repository.exists_by_email_hash(email_hash)

        # Assert
        assert exists is True

    async def test_exists_by_email_hash_false(self, repository):
        """Test that exists_by_email_hash returns False when user doesn't exist."""
        # Act
        exists = await repository.exists_by_email_hash("nonexistent_hash")

        # Assert
        assert exists is False

    async def test_delete_user_success(self, repository, db_session):
        """Test successful deletion of a user."""
        # Arrange
        email_hash = "delete_me_hash"
        created_user = await repository.create(email_hash=email_hash)
        await db_session.commit()

        # Act
        result = await repository.delete(created_user.user_id)
        await db_session.commit()

        # Assert
        assert result is True

        # Verify user is actually deleted
        found_user = await repository.get_by_id(created_user.user_id)
        assert found_user is None

    async def test_delete_user_not_found(self, repository):
        """Test that deleting a non-existent user returns False."""
        # Arrange
        nonexistent_id = uuid.uuid4()

        # Act
        result = await repository.delete(nonexistent_id)

        # Assert
        assert result is False
