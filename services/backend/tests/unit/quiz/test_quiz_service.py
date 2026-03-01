"""Tests for QuizService business logic."""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.quiz.services.quiz_service import QuizService
from app.modules.quiz.models import QuizState, QuizStatus, OwnershipRole, TaskType
from app.modules.quiz.schemas import (
    QuizCreationStatus,
    QuizDetailDto,
    QuizGenerationSpec,
)
from app.modules.quiz.exceptions import QuizNotFoundException, AccessDeniedException
from app.modules.quiz.constants import QUIZ_TITLE_PENDING
from app.modules.quiz.strategies import task_mapping_registry
from app.shared.ports.quiz_events import QuizDeletedEvent, QuizEventPublisher


pytestmark = pytest.mark.unit


@pytest.fixture
def mapping_registry():
    return task_mapping_registry()


@pytest.fixture
def mock_event_publisher() -> MagicMock:
    """Create mock quiz event publisher."""
    publisher = MagicMock(spec=QuizEventPublisher)
    publisher.publish_quiz_deleted = AsyncMock()
    return publisher


@pytest.fixture
def mock_generation_port() -> AsyncMock:
    """Create mock quiz generation port."""
    port = AsyncMock()
    port.generate_quiz = AsyncMock()
    return port


class TestQuizServiceListUserQuizzes:
    """Tests for QuizService.list_user_quizzes method."""

    @pytest.fixture
    def mock_db(self):
        return AsyncMock()

    @pytest.fixture
    def mock_quiz_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_ownership_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_task_repo(self):
        repo = AsyncMock()
        repo.list_types_by_quiz_ids = AsyncMock(return_value=[])
        return repo

    @pytest.fixture
    def mock_version_repo(self):
        return AsyncMock()

    @pytest.fixture
    def service(
        self,
        mock_db,
        mock_quiz_repo,
        mock_ownership_repo,
        mock_task_repo,
        mock_version_repo,
        mapping_registry,
        mock_event_publisher,
        mock_generation_port,
    ):
        return QuizService(
            mock_db,
            mock_quiz_repo,
            mock_ownership_repo,
            mock_task_repo,
            mock_version_repo,
            mapping_registry,
            mock_event_publisher,
            mock_generation_port,
        )

    @pytest.fixture
    def user_id(self):
        return uuid.uuid4()

    async def test_list_user_quizzes_returns_empty_list(
        self,
        service,
        mock_ownership_repo,
        user_id,
    ):
        mock_ownership_repo.get_quizzes_by_user.return_value = []

        result = await service.list_user_quizzes(user_id)

        assert isinstance(result, list)
        assert result == []
        mock_ownership_repo.get_quizzes_by_user.assert_called_once_with(user_id, None)

    async def test_list_user_quizzes_returns_quiz_list(
        self,
        service,
        mock_ownership_repo,
        user_id,
    ):
        quiz1 = MagicMock()
        quiz1.quiz_id = uuid.uuid4()
        quiz1.title = "Quiz 1"
        quiz1.topic = "Topic 1"
        quiz1.state = QuizState.PRIVATE
        quiz1.status = QuizStatus.PENDING
        quiz1.created_at = datetime(2024, 1, 1, 12, 0, 0)

        quiz2 = MagicMock()
        quiz2.quiz_id = uuid.uuid4()
        quiz2.title = "Quiz 2"
        quiz2.topic = "Topic 2"
        quiz2.state = QuizState.PUBLIC
        quiz2.status = QuizStatus.COMPLETED
        quiz2.created_at = datetime(2024, 1, 2, 12, 0, 0)

        mock_ownership_repo.get_quizzes_by_user.return_value = [
            (quiz1, OwnershipRole.OWNER),
            (quiz2, OwnershipRole.EDITOR),
        ]

        result = await service.list_user_quizzes(user_id)

        assert isinstance(result, list)
        assert len(result) == 2

    async def test_list_user_quizzes_maps_fields_correctly(
        self,
        service,
        mock_ownership_repo,
        user_id,
    ):
        quiz_id = uuid.uuid4()
        created_at = datetime(2024, 1, 1, 12, 0, 0)

        quiz = MagicMock()
        quiz.quiz_id = quiz_id
        quiz.title = "Test Quiz"
        quiz.topic = "Test Topic"
        quiz.state = QuizState.PROTECTED
        quiz.status = QuizStatus.COMPLETED
        quiz.created_at = created_at

        mock_ownership_repo.get_quizzes_by_user.return_value = [
            (quiz, OwnershipRole.VIEWER),
        ]

        result = await service.list_user_quizzes(user_id)

        item = result[0]
        assert item.quiz_id == quiz_id
        assert item.title == "Test Quiz"
        assert item.topic == "Test Topic"
        assert item.state == QuizState.PROTECTED
        assert item.status == QuizStatus.COMPLETED
        assert item.role == OwnershipRole.VIEWER
        assert item.created_at == created_at

    async def test_list_user_quizzes_filters_by_roles(
        self,
        service,
        mock_ownership_repo,
        user_id,
    ):
        mock_ownership_repo.get_quizzes_by_user.return_value = []

        await service.list_user_quizzes(
            user_id,
            roles=[OwnershipRole.OWNER, OwnershipRole.EDITOR],
        )

        mock_ownership_repo.get_quizzes_by_user.assert_called_once_with(
            user_id,
            [OwnershipRole.OWNER, OwnershipRole.EDITOR],
        )


class TestQuizServiceCreateQuiz:
    """Tests for QuizService.create_quiz method."""

    @pytest.fixture
    def mock_db(self):
        db = AsyncMock()
        db.commit = AsyncMock()
        return db

    @pytest.fixture
    def mock_quiz_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_ownership_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_task_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_version_repo(self):
        repo = AsyncMock()
        version = MagicMock()
        version.quiz_version_id = uuid.uuid4()
        repo.create_published.return_value = version
        return repo

    @pytest.fixture
    def mock_background_tasks(self):
        return MagicMock()

    @pytest.fixture
    def service(
        self,
        mock_db,
        mock_quiz_repo,
        mock_ownership_repo,
        mock_task_repo,
        mock_version_repo,
        mapping_registry,
        mock_event_publisher,
        mock_generation_port,
    ):
        return QuizService(
            mock_db,
            mock_quiz_repo,
            mock_ownership_repo,
            mock_task_repo,
            mock_version_repo,
            mapping_registry,
            mock_event_publisher,
            mock_generation_port,
        )

    @pytest.fixture
    def user_id(self):
        return uuid.uuid4()

    @pytest.fixture
    def generation_input(self):
        return QuizGenerationSpec(
            task_types=[TaskType.MULTIPLE_CHOICE],
            user_description="Math basics",
        )

    async def test_create_quiz_creates_quiz_with_pending_status(
        self,
        service,
        mock_quiz_repo,
        mock_ownership_repo,
        mock_background_tasks,
        mock_db,
        user_id,
        generation_input,
    ):
        quiz_id = uuid.uuid4()
        mock_quiz = MagicMock()
        mock_quiz.quiz_id = quiz_id
        mock_quiz.status = QuizStatus.PENDING
        mock_quiz_repo.create.return_value = mock_quiz

        await service.create_quiz(
            background_tasks=mock_background_tasks,
            user_id=user_id,
            generation_input=generation_input,
        )

        mock_quiz_repo.create.assert_called_once_with(
            title=QUIZ_TITLE_PENDING,
            created_by=user_id,
            topic="Math basics",
            status=QuizStatus.PENDING,
        )

    async def test_create_quiz_creates_ownership_with_owner_role(
        self,
        service,
        mock_quiz_repo,
        mock_ownership_repo,
        mock_background_tasks,
        mock_db,
        user_id,
        generation_input,
    ):
        quiz_id = uuid.uuid4()
        mock_quiz = MagicMock()
        mock_quiz.quiz_id = quiz_id
        mock_quiz.status = QuizStatus.PENDING
        mock_quiz_repo.create.return_value = mock_quiz

        await service.create_quiz(
            background_tasks=mock_background_tasks,
            user_id=user_id,
            generation_input=generation_input,
        )

        mock_ownership_repo.create.assert_called_once_with(
            quiz_id=quiz_id,
            user_id=user_id,
            role=OwnershipRole.OWNER,
        )

    async def test_create_quiz_commits_transaction(
        self,
        service,
        mock_quiz_repo,
        mock_ownership_repo,
        mock_background_tasks,
        mock_db,
        user_id,
        generation_input,
    ):
        mock_quiz = MagicMock()
        mock_quiz.quiz_id = uuid.uuid4()
        mock_quiz.status = QuizStatus.PENDING
        mock_quiz_repo.create.return_value = mock_quiz

        await service.create_quiz(
            background_tasks=mock_background_tasks,
            user_id=user_id,
            generation_input=generation_input,
        )

        mock_db.commit.assert_called_once()

    async def test_create_quiz_returns_correct_response(
        self,
        service,
        mock_quiz_repo,
        mock_ownership_repo,
        mock_background_tasks,
        mock_db,
        user_id,
        generation_input,
    ):
        quiz_id = uuid.uuid4()
        mock_quiz = MagicMock()
        mock_quiz.quiz_id = quiz_id
        mock_quiz.status = QuizStatus.PENDING
        mock_quiz_repo.create.return_value = mock_quiz

        result = await service.create_quiz(
            background_tasks=mock_background_tasks,
            user_id=user_id,
            generation_input=generation_input,
        )

        assert isinstance(result, QuizCreationStatus)
        assert result.quiz_id == quiz_id
        assert result.status == QuizStatus.PENDING

    async def test_create_quiz_schedules_background_task(
        self,
        service,
        mock_quiz_repo,
        mock_ownership_repo,
        mock_version_repo,
        mock_background_tasks,
        mock_db,
        user_id,
        generation_input,
    ):
        """Test that create_quiz schedules a background task for quiz generation."""
        quiz_id = uuid.uuid4()
        mock_quiz = MagicMock()
        mock_quiz.quiz_id = quiz_id
        mock_quiz.status = QuizStatus.PENDING
        mock_quiz_repo.create.return_value = mock_quiz

        await service.create_quiz(
            background_tasks=mock_background_tasks,
            user_id=user_id,
            generation_input=generation_input,
        )

        # Verify background task was scheduled
        mock_background_tasks.add_task.assert_called_once()
        call_args = mock_background_tasks.add_task.call_args
        assert call_args.kwargs["quiz_id"] == quiz_id
        assert (
            call_args.kwargs["quiz_version_id"]
            == mock_version_repo.create_published.return_value.quiz_version_id
        )
        assert call_args.kwargs["generation_input"] == generation_input
        assert call_args.kwargs["generation_port"] == service.generation_port

    async def test_create_quiz_uses_empty_topic_when_no_description(
        self,
        service,
        mock_quiz_repo,
        mock_ownership_repo,
        mock_background_tasks,
        mock_db,
        user_id,
    ):
        """Test that create_quiz uses empty topic when user_description is None."""
        mock_quiz = MagicMock()
        mock_quiz.quiz_id = uuid.uuid4()
        mock_quiz.status = QuizStatus.PENDING
        mock_quiz_repo.create.return_value = mock_quiz

        input_without_description = QuizGenerationSpec(
            task_types=[TaskType.FREE_TEXT],
            user_description=None,
        )

        await service.create_quiz(
            background_tasks=mock_background_tasks,
            user_id=user_id,
            generation_input=input_without_description,
        )

        mock_quiz_repo.create.assert_called_once_with(
            title=QUIZ_TITLE_PENDING,
            created_by=user_id,
            topic="",
            status=QuizStatus.PENDING,
        )


class TestQuizServiceGetQuizDetail:
    """Tests for QuizService.get_quiz_detail method."""

    @pytest.fixture
    def mock_db(self):
        return AsyncMock()

    @pytest.fixture
    def mock_quiz_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_ownership_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_task_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_version_repo(self):
        return AsyncMock()

    @pytest.fixture
    def service(
        self,
        mock_db,
        mock_quiz_repo,
        mock_ownership_repo,
        mock_task_repo,
        mock_version_repo,
        mapping_registry,
        mock_event_publisher,
        mock_generation_port,
    ):
        return QuizService(
            mock_db,
            mock_quiz_repo,
            mock_ownership_repo,
            mock_task_repo,
            mock_version_repo,
            mapping_registry,
            mock_event_publisher,
            mock_generation_port,
        )

    @pytest.fixture
    def quiz_id(self):
        return uuid.uuid4()

    @pytest.fixture
    def user_id(self):
        return uuid.uuid4()

    @pytest.fixture
    def sample_quiz(self, quiz_id, user_id):
        quiz = MagicMock()
        quiz.quiz_id = quiz_id
        quiz.title = "Test Quiz"
        quiz.topic = "Test Topic"
        quiz.state = QuizState.PRIVATE
        quiz.status = QuizStatus.COMPLETED
        quiz.created_at = datetime(2024, 1, 1, 12, 0, 0)
        quiz.created_by = user_id
        return quiz

    async def test_get_quiz_detail_raises_access_denied(
        self,
        service,
        mock_ownership_repo,
        mock_quiz_repo,
        quiz_id,
        user_id,
        sample_quiz,
    ):
        mock_ownership_repo.user_has_access.return_value = False
        mock_quiz_repo.get_by_id.return_value = sample_quiz

        with pytest.raises(AccessDeniedException) as exc_info:
            await service.get_quiz_detail(quiz_id, user_id)

        assert exc_info.value.message == "You do not have access to this quiz"
        mock_ownership_repo.user_has_access.assert_called_once_with(
            quiz_id=quiz_id,
            user_id=user_id,
        )

    async def test_get_quiz_detail_raises_not_found(
        self,
        service,
        mock_quiz_repo,
        quiz_id,
        user_id,
    ):
        mock_quiz_repo.get_by_id.return_value = None

        with pytest.raises(QuizNotFoundException):
            await service.get_quiz_detail(quiz_id, user_id)

        mock_quiz_repo.get_by_id.assert_called_once_with(quiz_id, load_tasks=False)

    async def test_get_quiz_detail_success(
        self,
        service,
        mock_ownership_repo,
        mock_quiz_repo,
        mock_task_repo,
        mock_version_repo,
        quiz_id,
        user_id,
        sample_quiz,
    ):
        mock_ownership_repo.user_has_access.return_value = True
        mock_quiz_repo.get_by_id.return_value = sample_quiz
        mock_version_repo.get_current_version_id.return_value = uuid.uuid4()
        mock_task_repo.get_by_quiz_version.return_value = []

        result = await service.get_quiz_detail(quiz_id, user_id)

        assert isinstance(result, QuizDetailDto)
        assert result.quiz_id == quiz_id
        assert result.title == "Test Quiz"
        assert result.topic == "Test Topic"
        assert result.tasks == []

    async def test_get_quiz_detail_includes_tasks(
        self,
        service,
        mock_ownership_repo,
        mock_quiz_repo,
        mock_task_repo,
        mock_version_repo,
        quiz_id,
        user_id,
        sample_quiz,
    ):
        mock_ownership_repo.user_has_access.return_value = True
        mock_quiz_repo.get_by_id.return_value = sample_quiz
        mock_version_repo.get_current_version_id.return_value = uuid.uuid4()

        # Create mock FreeTextTask (simplest to mock)
        from app.modules.quiz.models import FreeTextTask, TaskType

        mock_task = MagicMock(spec=FreeTextTask)
        mock_task.task_id = uuid.uuid4()
        mock_task.quiz_id = quiz_id
        mock_task.type = TaskType.FREE_TEXT
        mock_task.prompt = "What is 2+2?"
        mock_task.topic_detail = "Math"
        mock_task.order_index = 0
        mock_task.reference_answer = "4"

        mock_task_repo.get_by_quiz_version.return_value = [mock_task]

        result = await service.get_quiz_detail(quiz_id, user_id)

        assert len(result.tasks) == 1
        assert result.tasks[0].prompt == "What is 2+2?"

    async def test_get_quiz_detail_allows_public_quiz(
        self,
        service,
        mock_ownership_repo,
        mock_quiz_repo,
        mock_task_repo,
        mock_version_repo,
        quiz_id,
        user_id,
        sample_quiz,
    ):
        sample_quiz.state = QuizState.PUBLIC
        mock_ownership_repo.user_has_access.return_value = False
        mock_quiz_repo.get_by_id.return_value = sample_quiz
        mock_version_repo.get_current_version_id.return_value = uuid.uuid4()
        mock_task_repo.get_by_quiz_version.return_value = []

        result = await service.get_quiz_detail(quiz_id, user_id)

        assert result.quiz_id == quiz_id
        mock_ownership_repo.user_has_access.assert_not_called()


class TestQuizServiceDeleteQuiz:
    """Tests for QuizService.delete_quiz method."""

    @pytest.fixture
    def mock_db(self):
        db = AsyncMock()
        db.commit = AsyncMock()
        return db

    @pytest.fixture
    def mock_quiz_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_ownership_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_task_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_version_repo(self):
        return AsyncMock()

    @pytest.fixture
    def service(
        self,
        mock_db,
        mock_quiz_repo,
        mock_ownership_repo,
        mock_task_repo,
        mock_version_repo,
        mapping_registry,
        mock_event_publisher,
        mock_generation_port,
    ):
        return QuizService(
            mock_db,
            mock_quiz_repo,
            mock_ownership_repo,
            mock_task_repo,
            mock_version_repo,
            mapping_registry,
            mock_event_publisher,
            mock_generation_port,
        )

    @pytest.fixture
    def quiz_id(self):
        return uuid.uuid4()

    @pytest.fixture
    def user_id(self):
        return uuid.uuid4()

    async def test_delete_quiz_raises_access_denied_for_non_owner(
        self,
        service,
        mock_ownership_repo,
        quiz_id,
        user_id,
    ):
        mock_ownership_repo.user_has_access.return_value = False

        with pytest.raises(AccessDeniedException) as exc_info:
            await service.delete_quiz(quiz_id, user_id)

        assert exc_info.value.message == "Only the quiz owner can delete the quiz"
        mock_ownership_repo.user_has_access.assert_called_once_with(
            quiz_id=quiz_id,
            user_id=user_id,
            required_role=OwnershipRole.OWNER,
        )

    async def test_delete_quiz_raises_not_found(
        self,
        service,
        mock_ownership_repo,
        mock_quiz_repo,
        quiz_id,
        user_id,
    ):
        mock_ownership_repo.user_has_access.return_value = True
        mock_quiz_repo.delete.return_value = False

        with pytest.raises(QuizNotFoundException):
            await service.delete_quiz(quiz_id, user_id)

    async def test_delete_quiz_success(
        self,
        service,
        mock_ownership_repo,
        mock_quiz_repo,
        mock_db,
        quiz_id,
        user_id,
    ):
        mock_ownership_repo.user_has_access.return_value = True
        mock_quiz_repo.delete.return_value = True

        await service.delete_quiz(quiz_id, user_id)

        mock_quiz_repo.delete.assert_called_once_with(quiz_id)

    async def test_delete_quiz_publishes_event(
        self,
        service,
        mock_ownership_repo,
        mock_quiz_repo,
        mock_event_publisher,
        mock_db,
        quiz_id,
        user_id,
    ):
        mock_ownership_repo.user_has_access.return_value = True
        mock_quiz_repo.delete.return_value = True

        await service.delete_quiz(quiz_id, user_id)

        mock_event_publisher.publish_quiz_deleted.assert_awaited_once()
        event = mock_event_publisher.publish_quiz_deleted.call_args.args[0]
        assert isinstance(event, QuizDeletedEvent)
        assert event.quiz_id == quiz_id
        assert event.db is mock_db

    async def test_delete_quiz_commits_transaction(
        self,
        service,
        mock_ownership_repo,
        mock_quiz_repo,
        mock_db,
        quiz_id,
        user_id,
    ):
        mock_ownership_repo.user_has_access.return_value = True
        mock_quiz_repo.delete.return_value = True

        await service.delete_quiz(quiz_id, user_id)

        mock_db.commit.assert_called_once()
