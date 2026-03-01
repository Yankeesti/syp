"""Unit tests for ShareLinkRepository."""

import uuid
from datetime import datetime, timezone, timedelta

import pytest

from app.modules.quiz.repositories.share_link_repository import ShareLinkRepository
from app.modules.quiz.repositories.quiz_repository import QuizRepository


pytestmark = pytest.mark.unit


class TestShareLinkRepository:
    """Test suite for ShareLinkRepository."""

    @pytest.fixture
    def repository(self, db_session):
        """Create a repository instance for testing."""
        return ShareLinkRepository(db_session)

    @pytest.fixture
    def user_id(self):
        """Create a user ID for testing."""
        return uuid.uuid4()

    @pytest.fixture
    async def quiz_id(self, db_session, user_id):
        """Create a quiz for testing share links."""
        quiz_repo = QuizRepository(db_session)
        quiz = await quiz_repo.create("Test Quiz", user_id)
        await db_session.commit()
        return quiz.quiz_id

    # ==================== Create Tests ====================

    async def test_create_share_link_with_all_fields(
        self,
        repository,
        quiz_id,
        user_id,
        db_session,
    ):
        """Test creating a share link with all fields specified."""
        # Arrange
        token = "test_token_12345"
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        max_uses = 10

        # Act
        share_link = await repository.create(
            quiz_id=quiz_id,
            token=token,
            created_by=user_id,
            expires_at=expires_at,
            max_uses=max_uses,
        )
        await db_session.commit()

        # Assert
        assert share_link is not None
        assert isinstance(share_link.share_link_id, uuid.UUID)
        assert share_link.quiz_id == quiz_id
        assert share_link.token == token
        assert share_link.created_by == user_id
        # Compare datetime without timezone (DB may strip tzinfo)
        assert share_link.expires_at.replace(tzinfo=None) == expires_at.replace(
            tzinfo=None,
        )
        assert share_link.max_uses == max_uses
        assert share_link.current_uses == 0  # Default
        assert share_link.is_active is True  # Default
        assert share_link.created_at is not None

    async def test_create_share_link_with_defaults(
        self,
        repository,
        quiz_id,
        user_id,
        db_session,
    ):
        """Test creating a share link with None values (unlimited)."""
        # Arrange
        token = "unlimited_token"

        # Act
        share_link = await repository.create(
            quiz_id=quiz_id,
            token=token,
            created_by=user_id,
            expires_at=None,  # Never expires
            max_uses=None,  # Unlimited uses
        )
        await db_session.commit()

        # Assert
        assert share_link is not None
        assert share_link.token == token
        assert share_link.expires_at is None
        assert share_link.max_uses is None
        assert share_link.current_uses == 0
        assert share_link.is_active is True

    # ==================== Get by Token Tests ====================

    async def test_get_by_token_exists_active(
        self,
        repository,
        quiz_id,
        user_id,
        db_session,
    ):
        """Test retrieving an active share link by token."""
        # Arrange
        token = "active_token_123"
        created_link = await repository.create(
            quiz_id=quiz_id,
            token=token,
            created_by=user_id,
        )
        await db_session.commit()

        # Act
        found_link = await repository.get_by_token(token)

        # Assert
        assert found_link is not None
        assert found_link.share_link_id == created_link.share_link_id
        assert found_link.token == token
        assert found_link.is_active is True

    async def test_get_by_token_not_found(self, repository):
        """Test that get_by_token returns None when token doesn't exist."""
        # Act
        found_link = await repository.get_by_token("nonexistent_token")

        # Assert
        assert found_link is None

    async def test_get_by_token_inactive(
        self,
        repository,
        quiz_id,
        user_id,
        db_session,
    ):
        """Test that get_by_token returns None for inactive link."""
        # Arrange
        token = "inactive_token"
        share_link = await repository.create(
            quiz_id=quiz_id,
            token=token,
            created_by=user_id,
        )
        await db_session.commit()

        # Revoke the link
        await repository.revoke(share_link.share_link_id)
        await db_session.commit()

        # Act
        found_link = await repository.get_by_token(token)

        # Assert
        assert found_link is None  # Should not find inactive link

    # ==================== Get by ID Tests ====================

    async def test_get_by_id_exists(
        self,
        repository,
        quiz_id,
        user_id,
        db_session,
    ):
        """Test retrieving a share link by ID."""
        # Arrange
        created_link = await repository.create(
            quiz_id=quiz_id,
            token="test_token",
            created_by=user_id,
        )
        await db_session.commit()

        # Act
        found_link = await repository.get_by_id(created_link.share_link_id)

        # Assert
        assert found_link is not None
        assert found_link.share_link_id == created_link.share_link_id
        assert found_link.token == "test_token"

    async def test_get_by_id_not_found(self, repository):
        """Test that get_by_id returns None when ID doesn't exist."""
        # Act
        found_link = await repository.get_by_id(uuid.uuid4())

        # Assert
        assert found_link is None

    # ==================== Get by Quiz ID Tests ====================

    async def test_get_by_quiz_id_multiple_links(
        self,
        repository,
        quiz_id,
        user_id,
        db_session,
    ):
        """Test retrieving all share links for a quiz, ordered by created_at desc."""
        # Arrange
        link1 = await repository.create(
            quiz_id=quiz_id,
            token="first_token",
            created_by=user_id,
        )
        await db_session.flush()
        link2 = await repository.create(
            quiz_id=quiz_id,
            token="second_token",
            created_by=user_id,
        )
        await db_session.flush()
        link3 = await repository.create(
            quiz_id=quiz_id,
            token="third_token",
            created_by=user_id,
        )
        await db_session.commit()

        # Act
        links = await repository.get_by_quiz_id(quiz_id)

        # Assert - Most recent first
        assert len(links) == 3
        assert links[0].token == "third_token"
        assert links[1].token == "second_token"
        assert links[2].token == "first_token"

    async def test_get_by_quiz_id_empty(self, repository, quiz_id):
        """Test that get_by_quiz_id returns empty list when no links exist."""
        # Act
        links = await repository.get_by_quiz_id(quiz_id)

        # Assert
        assert links == []

    # ==================== Revoke Tests ====================

    async def test_revoke_share_link(
        self,
        repository,
        quiz_id,
        user_id,
        db_session,
    ):
        """Test revoking a share link by setting is_active to False."""
        # Arrange
        share_link = await repository.create(
            quiz_id=quiz_id,
            token="revoke_me",
            created_by=user_id,
        )
        await db_session.commit()
        assert share_link.is_active is True

        # Act
        await repository.revoke(share_link.share_link_id)
        await db_session.commit()

        # Assert
        revoked_link = await repository.get_by_id(share_link.share_link_id)
        assert revoked_link is not None
        assert revoked_link.is_active is False

    # ==================== Increment Uses Tests ====================

    async def test_increment_uses(
        self,
        repository,
        quiz_id,
        user_id,
        db_session,
    ):
        """Test incrementing the current_uses counter by 1."""
        # Arrange
        share_link = await repository.create(
            quiz_id=quiz_id,
            token="use_me",
            created_by=user_id,
            max_uses=5,
        )
        await db_session.commit()
        assert share_link.current_uses == 0

        # Act - Increment once
        await repository.increment_uses(share_link.share_link_id)
        await db_session.commit()

        # Assert
        updated_link = await repository.get_by_id(share_link.share_link_id)
        assert updated_link is not None
        assert updated_link.current_uses == 1

        # Act - Increment again
        await repository.increment_uses(share_link.share_link_id)
        await db_session.commit()

        # Assert
        updated_link = await repository.get_by_id(share_link.share_link_id)
        assert updated_link.current_uses == 2

    # ==================== Get by Token for Update Tests ====================

    async def test_get_by_token_for_update(
        self,
        repository,
        quiz_id,
        user_id,
        db_session,
    ):
        """Test getting a share link by token with row-level lock."""
        # Arrange
        token = "locked_token"
        created_link = await repository.create(
            quiz_id=quiz_id,
            token=token,
            created_by=user_id,
        )
        await db_session.commit()

        # Act
        locked_link = await repository.get_by_token_for_update(token)

        # Assert
        assert locked_link is not None
        assert locked_link.share_link_id == created_link.share_link_id
        assert locked_link.token == token
        assert locked_link.is_active is True
