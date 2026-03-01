"""Unit tests for QuizOwnershipRepository."""

import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app.modules.quiz.models.quiz import Quiz, QuizState, QuizStatus
from app.modules.quiz.models.quiz_ownership import OwnershipRole
from app.modules.quiz.repositories.quiz_ownership_repository import (
    QuizOwnershipRepository,
)


pytestmark = pytest.mark.unit


class TestQuizOwnershipRepository:
    """Test suite for QuizOwnershipRepository."""

    @pytest.fixture
    async def quiz(self, db_session):
        """Create a quiz for testing ownership."""
        quiz = Quiz(
            title="Test Quiz",
            topic="Testing",
            created_by=uuid.uuid4(),
            state=QuizState.PRIVATE,
            status=QuizStatus.PENDING,
        )
        db_session.add(quiz)
        await db_session.flush()
        await db_session.refresh(quiz)
        return quiz

    @pytest.fixture
    def repository(self, db_session):
        """Create a repository instance for testing."""
        return QuizOwnershipRepository(db_session)

    @pytest.fixture
    def user_id(self):
        """Create a user ID for testing."""
        return uuid.uuid4()

    # ==================== Create Tests ====================

    async def test_create_ownership_with_default_role(
        self,
        repository,
        quiz,
        user_id,
        db_session,
    ):
        """Test creating ownership with default OWNER role."""
        # Act
        ownership = await repository.create(
            quiz_id=quiz.quiz_id,
            user_id=user_id,
        )
        await db_session.commit()

        # Assert
        assert ownership is not None
        assert isinstance(ownership.ownership_id, uuid.UUID)
        assert ownership.quiz_id == quiz.quiz_id
        assert ownership.user_id == user_id
        assert ownership.role == OwnershipRole.OWNER  # Default
        assert ownership.created_at is not None
        assert ownership.updated_at is not None

    async def test_create_ownership_with_editor_role(
        self,
        repository,
        quiz,
        user_id,
        db_session,
    ):
        """Test creating ownership with EDITOR role."""
        # Act
        ownership = await repository.create(
            quiz_id=quiz.quiz_id,
            user_id=user_id,
            role=OwnershipRole.EDITOR,
        )
        await db_session.commit()

        # Assert
        assert ownership.role == OwnershipRole.EDITOR

    async def test_create_ownership_with_viewer_role(
        self,
        repository,
        quiz,
        user_id,
        db_session,
    ):
        """Test creating ownership with VIEWER role."""
        # Act
        ownership = await repository.create(
            quiz_id=quiz.quiz_id,
            user_id=user_id,
            role=OwnershipRole.VIEWER,
        )
        await db_session.commit()

        # Assert
        assert ownership.role == OwnershipRole.VIEWER

    async def test_create_duplicate_ownership_raises_error(
        self,
        repository,
        quiz,
        user_id,
        db_session,
    ):
        """Test that creating duplicate quiz+user ownership raises IntegrityError."""
        # Arrange
        await repository.create(quiz_id=quiz.quiz_id, user_id=user_id)
        await db_session.commit()

        # Act & Assert
        with pytest.raises(IntegrityError):
            await repository.create(quiz_id=quiz.quiz_id, user_id=user_id)
            await db_session.commit()

    # ==================== Get Tests ====================

    async def test_get_by_quiz_and_user_exists(
        self,
        repository,
        quiz,
        user_id,
        db_session,
    ):
        """Test retrieving ownership by quiz and user when it exists."""
        # Arrange
        created = await repository.create(
            quiz_id=quiz.quiz_id,
            user_id=user_id,
            role=OwnershipRole.EDITOR,
        )
        await db_session.commit()

        # Act
        found = await repository.get_by_quiz_and_user(quiz.quiz_id, user_id)

        # Assert
        assert found is not None
        assert found.ownership_id == created.ownership_id
        assert found.role == OwnershipRole.EDITOR

    async def test_get_by_quiz_and_user_not_found(
        self,
        repository,
        quiz,
        user_id,
    ):
        """Test that get_by_quiz_and_user returns None when not found."""
        # Act
        found = await repository.get_by_quiz_and_user(quiz.quiz_id, user_id)

        # Assert
        assert found is None

    async def test_get_by_quiz_and_user_wrong_user(
        self,
        repository,
        quiz,
        user_id,
        db_session,
    ):
        """Test that get_by_quiz_and_user returns None for wrong user."""
        # Arrange
        await repository.create(quiz_id=quiz.quiz_id, user_id=user_id)
        await db_session.commit()

        other_user_id = uuid.uuid4()

        # Act
        found = await repository.get_by_quiz_and_user(quiz.quiz_id, other_user_id)

        # Assert
        assert found is None

    # ==================== Access Check Tests ====================

    async def test_user_has_access_returns_true_when_any_role(
        self,
        repository,
        quiz,
        user_id,
        db_session,
    ):
        """Test user_has_access returns True when user has any ownership."""
        # Arrange
        await repository.create(
            quiz_id=quiz.quiz_id,
            user_id=user_id,
            role=OwnershipRole.VIEWER,
        )
        await db_session.commit()

        # Act
        has_access = await repository.user_has_access(quiz.quiz_id, user_id)

        # Assert
        assert has_access is True

    async def test_user_has_access_returns_false_when_no_ownership(
        self,
        repository,
        quiz,
        user_id,
    ):
        """Test user_has_access returns False when user has no ownership."""
        # Act
        has_access = await repository.user_has_access(quiz.quiz_id, user_id)

        # Assert
        assert has_access is False

    # ==================== Role Hierarchy Tests ====================

    async def test_user_has_access_owner_has_all_permissions(
        self,
        repository,
        quiz,
        user_id,
        db_session,
    ):
        """Test that OWNER role has access to all role levels."""
        # Arrange
        await repository.create(
            quiz_id=quiz.quiz_id,
            user_id=user_id,
            role=OwnershipRole.OWNER,
        )
        await db_session.commit()

        # Act & Assert
        assert await repository.user_has_access(
            quiz.quiz_id,
            user_id,
            required_role=OwnershipRole.VIEWER,
        )
        assert await repository.user_has_access(
            quiz.quiz_id,
            user_id,
            required_role=OwnershipRole.EDITOR,
        )
        assert await repository.user_has_access(
            quiz.quiz_id,
            user_id,
            required_role=OwnershipRole.OWNER,
        )

    async def test_user_has_access_editor_has_viewer_permission(
        self,
        repository,
        quiz,
        user_id,
        db_session,
    ):
        """Test that EDITOR role has VIEWER permission but not OWNER."""
        # Arrange
        await repository.create(
            quiz_id=quiz.quiz_id,
            user_id=user_id,
            role=OwnershipRole.EDITOR,
        )
        await db_session.commit()

        # Act & Assert
        assert await repository.user_has_access(
            quiz.quiz_id,
            user_id,
            required_role=OwnershipRole.VIEWER,
        )
        assert await repository.user_has_access(
            quiz.quiz_id,
            user_id,
            required_role=OwnershipRole.EDITOR,
        )
        assert not await repository.user_has_access(
            quiz.quiz_id,
            user_id,
            required_role=OwnershipRole.OWNER,
        )

    async def test_user_has_access_viewer_only_has_viewer_permission(
        self,
        repository,
        quiz,
        user_id,
        db_session,
    ):
        """Test that VIEWER role only has VIEWER permission."""
        # Arrange
        await repository.create(
            quiz_id=quiz.quiz_id,
            user_id=user_id,
            role=OwnershipRole.VIEWER,
        )
        await db_session.commit()

        # Act & Assert
        assert await repository.user_has_access(
            quiz.quiz_id,
            user_id,
            required_role=OwnershipRole.VIEWER,
        )
        assert not await repository.user_has_access(
            quiz.quiz_id,
            user_id,
            required_role=OwnershipRole.EDITOR,
        )
        assert not await repository.user_has_access(
            quiz.quiz_id,
            user_id,
            required_role=OwnershipRole.OWNER,
        )

    # ==================== Delete Tests ====================

    async def test_delete_by_quiz_removes_all_ownerships(
        self,
        repository,
        quiz,
        db_session,
    ):
        """Test that delete_by_quiz removes all ownership records for a quiz."""
        # Arrange
        user1 = uuid.uuid4()
        user2 = uuid.uuid4()
        user3 = uuid.uuid4()

        await repository.create(quiz_id=quiz.quiz_id, user_id=user1)
        await repository.create(
            quiz_id=quiz.quiz_id,
            user_id=user2,
            role=OwnershipRole.EDITOR,
        )
        await repository.create(
            quiz_id=quiz.quiz_id,
            user_id=user3,
            role=OwnershipRole.VIEWER,
        )
        await db_session.commit()

        # Act
        deleted_count = await repository.delete_by_quiz(quiz.quiz_id)
        await db_session.commit()

        # Assert
        assert deleted_count == 3
        assert await repository.get_by_quiz_and_user(quiz.quiz_id, user1) is None
        assert await repository.get_by_quiz_and_user(quiz.quiz_id, user2) is None
        assert await repository.get_by_quiz_and_user(quiz.quiz_id, user3) is None

    async def test_delete_by_quiz_returns_zero_when_no_ownerships(
        self,
        repository,
        quiz,
        db_session,
    ):
        """Test that delete_by_quiz returns 0 when no ownerships exist."""
        # Act
        deleted_count = await repository.delete_by_quiz(quiz.quiz_id)
        await db_session.commit()

        # Assert
        assert deleted_count == 0

    async def test_delete_by_quiz_does_not_affect_other_quizzes(
        self,
        repository,
        quiz,
        db_session,
    ):
        """Test that delete_by_quiz only affects the specified quiz."""
        # Arrange
        other_quiz = Quiz(
            title="Other Quiz",
            topic="Other",
            created_by=uuid.uuid4(),
            state=QuizState.PRIVATE,
            status=QuizStatus.PENDING,
        )
        db_session.add(other_quiz)
        await db_session.flush()

        user_id = uuid.uuid4()

        await repository.create(quiz_id=quiz.quiz_id, user_id=user_id)
        await repository.create(quiz_id=other_quiz.quiz_id, user_id=user_id)
        await db_session.commit()

        # Act
        await repository.delete_by_quiz(quiz.quiz_id)
        await db_session.commit()

        # Assert
        assert await repository.get_by_quiz_and_user(quiz.quiz_id, user_id) is None
        assert (
            await repository.get_by_quiz_and_user(other_quiz.quiz_id, user_id)
            is not None
        )
