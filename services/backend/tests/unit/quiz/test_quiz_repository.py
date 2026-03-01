"""Unit tests for QuizRepository."""

import uuid

import pytest

from app.modules.quiz.models.quiz import Quiz, QuizState, QuizStatus
from app.modules.quiz.repositories.quiz_repository import QuizRepository


pytestmark = pytest.mark.unit


class TestQuizRepository:
    """Test suite for QuizRepository."""

    @pytest.fixture
    def repository(self, db_session):
        """Create a repository instance for testing."""
        return QuizRepository(db_session)

    @pytest.fixture
    def user_id(self):
        """Create a user ID for testing."""
        return uuid.uuid4()

    # ==================== Create Tests ====================

    async def test_create_quiz_with_defaults(self, repository, user_id, db_session):
        """Test creating a quiz with default values."""
        # Act
        quiz = await repository.create(
            title="My Quiz",
            created_by=user_id,
        )
        await db_session.commit()

        # Assert
        assert quiz is not None
        assert isinstance(quiz.quiz_id, uuid.UUID)
        assert quiz.title == "My Quiz"
        assert quiz.topic == ""  # Default empty string
        assert quiz.state == QuizState.PRIVATE  # Default
        assert quiz.status == QuizStatus.PENDING  # Default
        assert quiz.created_by == user_id
        assert quiz.created_at is not None
        assert quiz.updated_at is not None

    async def test_create_quiz_with_all_fields(self, repository, user_id, db_session):
        """Test creating a quiz with all fields specified."""
        # Act
        quiz = await repository.create(
            title="Advanced Quiz",
            created_by=user_id,
            topic="Machine Learning",
            state=QuizState.PROTECTED,
            status=QuizStatus.COMPLETED,
        )
        await db_session.commit()

        # Assert
        assert quiz.title == "Advanced Quiz"
        assert quiz.topic == "Machine Learning"
        assert quiz.state == QuizState.PROTECTED
        assert quiz.status == QuizStatus.COMPLETED

    # ==================== Get by ID Tests ====================

    async def test_get_by_id_exists(self, repository, user_id, db_session):
        """Test retrieving a quiz by ID when it exists."""
        # Arrange
        created_quiz = await repository.create(
            title="Test Quiz",
            created_by=user_id,
            topic="Testing",
        )
        await db_session.commit()

        # Act
        found_quiz = await repository.get_by_id(created_quiz.quiz_id)

        # Assert
        assert found_quiz is not None
        assert found_quiz.quiz_id == created_quiz.quiz_id
        assert found_quiz.title == "Test Quiz"

    async def test_get_by_id_not_found(self, repository):
        """Test that get_by_id returns None when quiz doesn't exist."""
        # Act
        found_quiz = await repository.get_by_id(uuid.uuid4())

        # Assert
        assert found_quiz is None

    async def test_get_by_id_with_load_tasks(self, repository, user_id, db_session):
        """Test that load_tasks parameter loads tasks relationship."""
        # Arrange
        quiz = await repository.create(
            title="Quiz with Tasks",
            created_by=user_id,
        )
        await db_session.commit()

        # Act
        found_quiz = await repository.get_by_id(quiz.quiz_id, load_tasks=True)

        # Assert
        assert found_quiz is not None
        assert found_quiz.tasks is not None  # Relationship loaded
        assert isinstance(found_quiz.tasks, list)
        assert len(found_quiz.tasks) == 0  # No tasks yet

    # ==================== Get by User Tests ====================

    async def test_get_by_user_returns_user_quizzes(
        self,
        repository,
        user_id,
        db_session,
    ):
        """Test retrieving all quizzes by user."""
        # Arrange
        other_user_id = uuid.uuid4()

        await repository.create(title="Quiz 1", created_by=user_id)
        await repository.create(title="Quiz 2", created_by=user_id)
        await repository.create(title="Other User Quiz", created_by=other_user_id)
        await db_session.commit()

        # Act
        quizzes = await repository.get_by_user(user_id)

        # Assert
        assert len(quizzes) == 2
        assert all(q.created_by == user_id for q in quizzes)

    async def test_get_by_user_ordered_by_created_at_desc(
        self,
        repository,
        user_id,
        db_session,
    ):
        """Test that quizzes are returned in descending order by created_at."""
        # Arrange
        quiz1 = await repository.create(title="First", created_by=user_id)
        await db_session.flush()
        quiz2 = await repository.create(title="Second", created_by=user_id)
        await db_session.flush()
        quiz3 = await repository.create(title="Third", created_by=user_id)
        await db_session.commit()

        # Act
        quizzes = await repository.get_by_user(user_id)

        # Assert - Most recent first
        assert len(quizzes) == 3
        assert quizzes[0].title == "Third"
        assert quizzes[1].title == "Second"
        assert quizzes[2].title == "First"

    async def test_get_by_user_filter_by_state(
        self,
        repository,
        user_id,
        db_session,
    ):
        """Test filtering quizzes by state."""
        # Arrange
        await repository.create(
            title="Private Quiz",
            created_by=user_id,
            state=QuizState.PRIVATE,
        )
        await repository.create(
            title="Public Quiz",
            created_by=user_id,
            state=QuizState.PUBLIC,
        )
        await db_session.commit()

        # Act
        private_quizzes = await repository.get_by_user(user_id, state=QuizState.PRIVATE)
        public_quizzes = await repository.get_by_user(user_id, state=QuizState.PUBLIC)

        # Assert
        assert len(private_quizzes) == 1
        assert private_quizzes[0].title == "Private Quiz"

        assert len(public_quizzes) == 1
        assert public_quizzes[0].title == "Public Quiz"

    async def test_get_by_user_filter_by_status(
        self,
        repository,
        user_id,
        db_session,
    ):
        """Test filtering quizzes by status."""
        # Arrange
        await repository.create(
            title="Pending Quiz",
            created_by=user_id,
            status=QuizStatus.PENDING,
        )
        await repository.create(
            title="Completed Quiz",
            created_by=user_id,
            status=QuizStatus.COMPLETED,
        )
        await db_session.commit()

        # Act
        pending = await repository.get_by_user(user_id, status=QuizStatus.PENDING)
        completed = await repository.get_by_user(user_id, status=QuizStatus.COMPLETED)

        # Assert
        assert len(pending) == 1
        assert pending[0].title == "Pending Quiz"

        assert len(completed) == 1
        assert completed[0].title == "Completed Quiz"

    async def test_get_by_user_filter_by_state_and_status(
        self,
        repository,
        user_id,
        db_session,
    ):
        """Test filtering quizzes by both state and status."""
        # Arrange
        await repository.create(
            title="Target",
            created_by=user_id,
            state=QuizState.PUBLIC,
            status=QuizStatus.COMPLETED,
        )
        await repository.create(
            title="Wrong State",
            created_by=user_id,
            state=QuizState.PRIVATE,
            status=QuizStatus.COMPLETED,
        )
        await repository.create(
            title="Wrong Status",
            created_by=user_id,
            state=QuizState.PUBLIC,
            status=QuizStatus.PENDING,
        )
        await db_session.commit()

        # Act
        quizzes = await repository.get_by_user(
            user_id,
            state=QuizState.PUBLIC,
            status=QuizStatus.COMPLETED,
        )

        # Assert
        assert len(quizzes) == 1
        assert quizzes[0].title == "Target"

    async def test_get_by_user_empty(self, repository, user_id):
        """Test that get_by_user returns empty list for user without quizzes."""
        # Act
        quizzes = await repository.get_by_user(user_id)

        # Assert
        assert quizzes == []

    # ==================== Update Tests ====================

    async def test_update_status_success(self, repository, user_id, db_session):
        """Test updating quiz status."""
        # Arrange
        quiz = await repository.create(
            title="Quiz",
            created_by=user_id,
            status=QuizStatus.PENDING,
        )
        await db_session.commit()

        # Act
        updated = await repository.update_status(quiz.quiz_id, QuizStatus.GENERATING)
        await db_session.commit()

        # Assert
        assert updated is not None
        assert updated.status == QuizStatus.GENERATING

    async def test_update_status_not_found(self, repository):
        """Test that update_status returns None for non-existent quiz."""
        # Act
        result = await repository.update_status(uuid.uuid4(), QuizStatus.COMPLETED)

        # Assert
        assert result is None

    async def test_update_state_success(self, repository, user_id, db_session):
        """Test updating quiz state."""
        # Arrange
        quiz = await repository.create(
            title="Quiz",
            created_by=user_id,
            state=QuizState.PRIVATE,
        )
        await db_session.commit()

        # Act
        updated = await repository.update_state(quiz.quiz_id, QuizState.PUBLIC)
        await db_session.commit()

        # Assert
        assert updated is not None
        assert updated.state == QuizState.PUBLIC

    async def test_update_state_not_found(self, repository):
        """Test that update_state returns None for non-existent quiz."""
        # Act
        result = await repository.update_state(uuid.uuid4(), QuizState.PUBLIC)

        # Assert
        assert result is None

    # ==================== Delete Tests ====================

    async def test_delete_success(self, repository, user_id, db_session):
        """Test successful deletion of a quiz."""
        # Arrange
        quiz = await repository.create(title="Delete Me", created_by=user_id)
        await db_session.commit()
        quiz_id = quiz.quiz_id

        # Act
        result = await repository.delete(quiz_id)
        await db_session.commit()

        # Assert
        assert result is True
        found = await repository.get_by_id(quiz_id)
        assert found is None

    async def test_delete_not_found(self, repository):
        """Test that deleting non-existent quiz returns False."""
        # Act
        result = await repository.delete(uuid.uuid4())

        # Assert
        assert result is False
