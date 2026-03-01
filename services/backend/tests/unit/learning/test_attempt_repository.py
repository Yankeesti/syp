"""Tests for AttemptRepository."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.learning.models import Attempt, AttemptStatus
from app.modules.learning.repositories.attempt_repository import AttemptRepository


pytestmark = pytest.mark.unit


class TestAttemptRepository:
    """Tests for AttemptRepository."""

    @pytest.fixture
    def repository(self, db_session: AsyncSession) -> AttemptRepository:
        """Create AttemptRepository instance."""
        return AttemptRepository(db_session)

    @pytest.fixture
    def user_id(self):
        """Create a user ID for testing."""
        return uuid.uuid4()

    @pytest.fixture
    def quiz_id(self):
        """Create a quiz ID for testing."""
        return uuid.uuid4()

    # ==================== Create Tests ====================

    async def test_create_attempt(
        self,
        repository: AttemptRepository,
        user_id: uuid.UUID,
        quiz_id: uuid.UUID,
        db_session: AsyncSession,
    ):
        """Test creating a new attempt."""
        # Act
        attempt = await repository.create_attempt(user_id, quiz_id)
        await db_session.commit()

        # Assert
        assert attempt.attempt_id is not None
        assert attempt.user_id == user_id
        assert attempt.quiz_id == quiz_id
        assert attempt.status == AttemptStatus.IN_PROGRESS
        assert attempt.started_at is not None
        assert attempt.evaluated_at is None
        assert attempt.total_percentage is None

    # ==================== Get Open Attempt Tests ====================

    async def test_get_open_attempt_exists(
        self,
        repository: AttemptRepository,
        user_id: uuid.UUID,
        quiz_id: uuid.UUID,
        db_session: AsyncSession,
    ):
        """Test getting an existing open attempt."""
        # Arrange - Create attempt
        created = await repository.create_attempt(user_id, quiz_id)
        await db_session.commit()

        # Act - Get open attempt
        found = await repository.get_open_attempt(user_id, quiz_id)

        # Assert
        assert found is not None
        assert found.attempt_id == created.attempt_id

    async def test_get_open_attempt_not_exists(
        self,
        repository: AttemptRepository,
    ):
        """Test getting non-existent open attempt returns None."""
        # Act
        result = await repository.get_open_attempt(uuid.uuid4(), uuid.uuid4())

        # Assert
        assert result is None

    async def test_get_open_attempt_ignores_evaluated(
        self,
        repository: AttemptRepository,
        user_id: uuid.UUID,
        quiz_id: uuid.UUID,
        db_session: AsyncSession,
    ):
        """Test that evaluated attempts are not returned as open."""
        # Arrange - Create and evaluate attempt
        attempt = await repository.create_attempt(user_id, quiz_id)
        await repository.mark_evaluated(
            attempt.attempt_id,
            Decimal("75.00"),
            datetime.now(timezone.utc),
        )
        await db_session.commit()

        # Act - Should not find open attempt
        found = await repository.get_open_attempt(user_id, quiz_id)

        # Assert
        assert found is None

    async def test_get_open_attempt_ignores_other_users(
        self,
        repository: AttemptRepository,
        quiz_id: uuid.UUID,
        db_session: AsyncSession,
    ):
        """Test that open attempts from other users are not returned."""
        # Arrange
        user1_id = uuid.uuid4()
        user2_id = uuid.uuid4()

        await repository.create_attempt(user1_id, quiz_id)
        await db_session.commit()

        # Act - User 2 tries to get open attempt
        found = await repository.get_open_attempt(user2_id, quiz_id)

        # Assert
        assert found is None

    async def test_get_open_attempt_ignores_other_quizzes(
        self,
        repository: AttemptRepository,
        user_id: uuid.UUID,
        db_session: AsyncSession,
    ):
        """Test that open attempts for other quizzes are not returned."""
        # Arrange
        quiz1_id = uuid.uuid4()
        quiz2_id = uuid.uuid4()

        await repository.create_attempt(user_id, quiz1_id)
        await db_session.commit()

        # Act - Try to get open attempt for different quiz
        found = await repository.get_open_attempt(user_id, quiz2_id)

        # Assert
        assert found is None

    # ==================== Get by ID Tests ====================

    async def test_get_by_id(
        self,
        repository: AttemptRepository,
        user_id: uuid.UUID,
        quiz_id: uuid.UUID,
        db_session: AsyncSession,
    ):
        """Test getting attempt by ID."""
        # Arrange
        created = await repository.create_attempt(user_id, quiz_id)
        await db_session.commit()

        # Act
        found = await repository.get_by_id(created.attempt_id)

        # Assert
        assert found is not None
        assert found.attempt_id == created.attempt_id

    async def test_get_by_id_not_found(self, repository: AttemptRepository):
        """Test getting non-existent attempt returns None."""
        # Act
        result = await repository.get_by_id(uuid.uuid4())

        # Assert
        assert result is None

    async def test_get_by_id_with_answers(
        self,
        repository: AttemptRepository,
        user_id: uuid.UUID,
        quiz_id: uuid.UUID,
        db_session: AsyncSession,
    ):
        """Test getting attempt by ID with answers loaded."""
        # Arrange
        created = await repository.create_attempt(user_id, quiz_id)
        await db_session.commit()

        # Act
        found = await repository.get_by_id_with_answers(created.attempt_id)

        # Assert
        assert found is not None
        assert found.attempt_id == created.attempt_id
        assert hasattr(found, "answers")
        assert isinstance(found.answers, list)
        assert len(found.answers) == 0  # No answers yet

    # ==================== Mark Evaluated Tests ====================

    async def test_mark_evaluated(
        self,
        repository: AttemptRepository,
        user_id: uuid.UUID,
        quiz_id: uuid.UUID,
        db_session: AsyncSession,
    ):
        """Test marking attempt as evaluated."""
        # Arrange
        total = Decimal("85.50")
        evaluated_at = datetime.now(timezone.utc)

        attempt = await repository.create_attempt(user_id, quiz_id)
        await db_session.commit()

        # Act
        await repository.mark_evaluated(attempt.attempt_id, total, evaluated_at)
        await db_session.commit()

        # Assert
        found = await repository.get_by_id(attempt.attempt_id)
        assert found.status == AttemptStatus.EVALUATED
        assert found.total_percentage == total
        assert found.evaluated_at is not None

    async def test_mark_evaluated_not_found(
        self,
        repository: AttemptRepository,
        db_session: AsyncSession,
    ):
        """Test marking non-existent attempt as evaluated does nothing."""
        # Act
        await repository.mark_evaluated(
            uuid.uuid4(),
            Decimal("100.0"),
            datetime.now(timezone.utc),
        )
        await db_session.commit()

        # Assert - No error raised

    # ==================== Delete Tests ====================

    async def test_delete_by_quiz_id(
        self,
        repository: AttemptRepository,
        quiz_id: uuid.UUID,
        db_session: AsyncSession,
    ):
        """Test deleting attempts by quiz ID."""
        # Arrange - Create multiple attempts for the same quiz
        user1_id = uuid.uuid4()
        user2_id = uuid.uuid4()

        await repository.create_attempt(user1_id, quiz_id)
        await repository.create_attempt(user2_id, quiz_id)
        await db_session.commit()

        # Act
        count = await repository.delete_by_quiz_id(quiz_id)
        await db_session.commit()

        # Assert
        assert count == 2

        # Verify deleted
        found = await repository.get_open_attempt(user1_id, quiz_id)
        assert found is None

    async def test_delete_by_quiz_id_no_attempts(
        self,
        repository: AttemptRepository,
        db_session: AsyncSession,
    ):
        """Test deleting by quiz ID when no attempts exist."""
        # Act
        count = await repository.delete_by_quiz_id(uuid.uuid4())
        await db_session.commit()

        # Assert
        assert count == 0

    async def test_delete_by_quiz_id_only_deletes_target_quiz(
        self,
        repository: AttemptRepository,
        user_id: uuid.UUID,
        db_session: AsyncSession,
    ):
        """Test that delete only removes attempts for the specified quiz."""
        # Arrange
        quiz1_id = uuid.uuid4()
        quiz2_id = uuid.uuid4()

        await repository.create_attempt(user_id, quiz1_id)
        await repository.create_attempt(user_id, quiz2_id)
        await db_session.commit()

        # Act - Delete only quiz1 attempts
        count = await repository.delete_by_quiz_id(quiz1_id)
        await db_session.commit()

        # Assert
        assert count == 1

        # Verify quiz1 attempt is deleted
        found1 = await repository.get_open_attempt(user_id, quiz1_id)
        assert found1 is None

        # Verify quiz2 attempt still exists
        found2 = await repository.get_open_attempt(user_id, quiz2_id)
        assert found2 is not None

    # ==================== List by User Tests ====================

    async def test_list_by_user_returns_all_attempts(
        self,
        repository: AttemptRepository,
        user_id: uuid.UUID,
        db_session: AsyncSession,
    ):
        """Test getting all attempts for a user."""
        # Arrange - Create attempts for different quizzes
        quiz1_id = uuid.uuid4()
        quiz2_id = uuid.uuid4()
        attempt1 = await repository.create_attempt(user_id, quiz1_id)
        attempt2 = await repository.create_attempt(user_id, quiz2_id)
        await db_session.commit()

        # Act
        attempts = await repository.list_by_user(user_id)

        # Assert
        assert len(attempts) == 2
        attempt_ids = [a.attempt_id for a in attempts]
        assert attempt1.attempt_id in attempt_ids
        assert attempt2.attempt_id in attempt_ids

    async def test_list_by_user_empty(
        self,
        repository: AttemptRepository,
    ):
        """Test getting attempts when none exist returns empty list."""
        # Act
        attempts = await repository.list_by_user(uuid.uuid4())

        # Assert
        assert attempts == []

    async def test_list_by_user_filter_by_quiz(
        self,
        repository: AttemptRepository,
        user_id: uuid.UUID,
        db_session: AsyncSession,
    ):
        """Test filtering attempts by quiz_id."""
        # Arrange
        quiz1_id = uuid.uuid4()
        quiz2_id = uuid.uuid4()

        await repository.create_attempt(user_id, quiz1_id)
        await repository.create_attempt(user_id, quiz2_id)
        await db_session.commit()

        # Act - Get only quiz1's attempts
        attempts = await repository.list_by_user(user_id, quiz_id=quiz1_id)

        # Assert
        assert len(attempts) == 1
        assert attempts[0].quiz_id == quiz1_id

    async def test_list_by_user_filter_by_status(
        self,
        repository: AttemptRepository,
        user_id: uuid.UUID,
        quiz_id: uuid.UUID,
        db_session: AsyncSession,
    ):
        """Test filtering attempts by status."""
        # Arrange - Create one evaluated and one in_progress
        attempt1 = await repository.create_attempt(user_id, quiz_id)
        await repository.mark_evaluated(
            attempt1.attempt_id,
            Decimal("80.00"),
            datetime.now(timezone.utc),
        )
        attempt2 = await repository.create_attempt(user_id, quiz_id)
        await db_session.commit()

        # Act - Get only in_progress attempts
        attempts = await repository.list_by_user(
            user_id,
            status=AttemptStatus.IN_PROGRESS,
        )

        # Assert
        assert len(attempts) == 1
        assert attempts[0].attempt_id == attempt2.attempt_id
        assert attempts[0].status == AttemptStatus.IN_PROGRESS

    async def test_list_by_user_filter_by_quiz_and_status(
        self,
        repository: AttemptRepository,
        user_id: uuid.UUID,
        db_session: AsyncSession,
    ):
        """Test filtering attempts by both quiz_id and status."""
        # Arrange
        quiz1_id = uuid.uuid4()
        quiz2_id = uuid.uuid4()

        attempt1 = await repository.create_attempt(user_id, quiz1_id)
        await repository.mark_evaluated(
            attempt1.attempt_id,
            Decimal("90.00"),
            datetime.now(timezone.utc),
        )
        await repository.create_attempt(user_id, quiz1_id)  # in_progress
        await repository.create_attempt(user_id, quiz2_id)  # in_progress
        await db_session.commit()

        # Act - Get only evaluated attempts for quiz1
        attempts = await repository.list_by_user(
            user_id,
            quiz_id=quiz1_id,
            status=AttemptStatus.EVALUATED,
        )

        # Assert
        assert len(attempts) == 1
        assert attempts[0].attempt_id == attempt1.attempt_id

    async def test_list_by_user_ordered_by_date_desc(
        self,
        repository: AttemptRepository,
        user_id: uuid.UUID,
        quiz_id: uuid.UUID,
        db_session: AsyncSession,
    ):
        """Test that attempts are ordered by started_at descending."""
        # Arrange - Create attempts sequentially
        attempt1 = await repository.create_attempt(user_id, quiz_id)
        await repository.mark_evaluated(
            attempt1.attempt_id,
            Decimal("50.00"),
            datetime.now(timezone.utc),
        )
        await db_session.commit()

        attempt2 = await repository.create_attempt(user_id, quiz_id)
        await db_session.commit()

        # Act
        attempts = await repository.list_by_user(user_id)

        # Assert - Newest first
        assert len(attempts) == 2
        assert attempts[0].attempt_id == attempt2.attempt_id
        assert attempts[1].attempt_id == attempt1.attempt_id

    async def test_list_by_user_ignores_other_users(
        self,
        repository: AttemptRepository,
        quiz_id: uuid.UUID,
        db_session: AsyncSession,
    ):
        """Test that only attempts from the specified user are returned."""
        # Arrange
        user1_id = uuid.uuid4()
        user2_id = uuid.uuid4()

        await repository.create_attempt(user1_id, quiz_id)
        await repository.create_attempt(user2_id, quiz_id)
        await db_session.commit()

        # Act - Get only user1's attempts
        attempts = await repository.list_by_user(user1_id)

        # Assert
        assert len(attempts) == 1
        assert attempts[0].user_id == user1_id
