"""Tests for AttemptAnswerService."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.learning.exceptions import (
    AttemptNotFoundException,
    AttemptLockedException,
    QuizNotCompletedException,
    AccessDeniedException,
    TaskNotFoundException,
    AnswerTypeMismatchException,
)
from app.modules.learning.models import Attempt, AttemptStatus, FreeTextAnswer
from app.modules.learning.repositories import AttemptRepository, AnswerRepository
from app.modules.learning.services import AttemptAnswerService
from app.modules.learning.strategies import (
    answer_mapping_registry,
    answer_upsert_registry,
)
from app.modules.learning.schemas.answer import (
    MultipleChoiceAnswerUpsert,
    FreeTextAnswerUpsert,
    ClozeAnswerUpsert,
    MultipleChoiceAnswerData,
    FreeTextAnswerData,
    ClozeAnswerData,
    ClozeItemData,
)
from app.modules.quiz.exceptions import (
    AccessDeniedException as QuizAccessDeniedException,
    QuizNotFoundException as QuizModuleNotFoundException,
    TaskNotFoundException as QuizModuleTaskNotFoundException,
)
from app.modules.quiz.models import QuizState, QuizStatus
from app.shared.ports.quiz_read import QuizReadPort
from app.modules.quiz.schemas import (
    QuizAccessDto,
    MultipleChoiceTaskResponse,
    FreeTextTaskResponse,
    ClozeTaskResponse,
)


@pytest.fixture
def mock_db_session() -> AsyncMock:
    """Create mock database session."""
    session = AsyncMock(spec=AsyncSession)
    session.commit = AsyncMock()
    return session


@pytest.fixture
def mock_quiz_read_port() -> MagicMock:
    """Create mock quiz read port."""
    return MagicMock(spec=QuizReadPort)


@pytest.fixture
def mock_attempt_repo() -> MagicMock:
    """Create mock attempt repository."""
    return MagicMock(spec=AttemptRepository)


@pytest.fixture
def mock_answer_repo() -> MagicMock:
    """Create mock answer repository."""
    return MagicMock(spec=AnswerRepository)


@pytest.fixture
def service(
    mock_db_session: AsyncMock,
    mock_quiz_read_port: MagicMock,
    mock_attempt_repo: MagicMock,
    mock_answer_repo: MagicMock,
) -> AttemptAnswerService:
    """Create service with mocked dependencies."""
    return AttemptAnswerService(
        mock_db_session,
        mock_quiz_read_port,
        answer_upsert_registry(),
        answer_mapping_registry(),
        mock_attempt_repo,
        mock_answer_repo,
    )


@pytest.fixture
def sample_attempt() -> Attempt:
    """Create a sample attempt."""
    attempt = MagicMock(spec=Attempt)
    attempt.attempt_id = uuid.uuid4()
    attempt.quiz_id = uuid.uuid4()
    attempt.user_id = uuid.uuid4()
    attempt.status = AttemptStatus.IN_PROGRESS
    attempt.started_at = datetime.now(timezone.utc)
    return attempt


@pytest.fixture
def sample_task() -> MultipleChoiceTaskResponse:
    """Create a sample task."""
    return MultipleChoiceTaskResponse(
        task_id=uuid.uuid4(),
        quiz_id=uuid.uuid4(),
        prompt="Prompt",
        topic_detail="Topic",
        order_index=0,
        type="multiple_choice",
        options=[],
    )


class TestStartOrResumeAttempt:
    """Tests for start_or_resume_attempt method."""

    async def test_start_new_attempt_success(
        self,
        service: AttemptAnswerService,
    ):
        """Test starting a new attempt successfully."""
        user_id = uuid.uuid4()
        quiz_id = uuid.uuid4()

        # Mock dependencies
        quiz_access = QuizAccessDto(
            quiz_id=quiz_id,
            status=QuizStatus.COMPLETED,
            state=QuizState.PUBLIC,
        )
        service.quiz_read_port.get_quiz_access = AsyncMock(
            return_value=quiz_access,
        )
        service.attempt_repo.get_open_attempt = AsyncMock(return_value=None)

        new_attempt = MagicMock(spec=Attempt)
        new_attempt.attempt_id = uuid.uuid4()
        new_attempt.quiz_id = quiz_id
        new_attempt.status = AttemptStatus.IN_PROGRESS
        new_attempt.started_at = datetime.now(timezone.utc)
        service.attempt_repo.create_attempt = AsyncMock(return_value=new_attempt)

        result, is_new = await service.start_or_resume_attempt(
            user_id,
            quiz_id,
        )

        assert is_new is True
        assert result.attempt_id == new_attempt.attempt_id
        service.attempt_repo.create_attempt.assert_called_once()

    async def test_resume_existing_attempt(
        self,
        service: AttemptAnswerService,
        sample_attempt: Attempt,
    ):
        """Test resuming an existing in_progress attempt."""
        user_id = sample_attempt.user_id
        quiz_id = uuid.uuid4()
        sample_attempt.quiz_id = quiz_id

        quiz_access = QuizAccessDto(
            quiz_id=quiz_id,
            status=QuizStatus.COMPLETED,
            state=QuizState.PUBLIC,
        )
        service.quiz_read_port.get_quiz_access = AsyncMock(
            return_value=quiz_access,
        )
        service.attempt_repo.get_open_attempt = AsyncMock(return_value=sample_attempt)
        service.answer_repo.list_by_attempt = AsyncMock(return_value=[])
        service.attempt_repo.create_attempt = (
            AsyncMock()
        )  # Mock to check it's not called

        result, is_new = await service.start_or_resume_attempt(
            user_id,
            quiz_id,
        )

        assert is_new is False
        assert result.attempt_id == sample_attempt.attempt_id
        service.attempt_repo.create_attempt.assert_not_called()

    async def test_quiz_not_found_raises_exception(
        self,
        service: AttemptAnswerService,
    ):
        """Test that QuizNotFoundException is raised when quiz doesn't exist."""
        service.quiz_read_port.get_quiz_access = AsyncMock(
            side_effect=QuizModuleNotFoundException(),
        )

        with pytest.raises(QuizModuleNotFoundException):
            await service.start_or_resume_attempt(uuid.uuid4(), uuid.uuid4())

    async def test_quiz_not_completed_raises_exception(
        self,
        service: AttemptAnswerService,
    ):
        """Test that QuizNotCompletedException is raised when quiz is not completed."""
        quiz_access = QuizAccessDto(
            quiz_id=uuid.uuid4(),
            status=QuizStatus.PENDING,
            state=QuizState.PUBLIC,
        )
        service.quiz_read_port.get_quiz_access = AsyncMock(
            return_value=quiz_access,
        )

        with pytest.raises(QuizNotCompletedException):
            await service.start_or_resume_attempt(uuid.uuid4(), quiz_access.quiz_id)

    async def test_access_denied_private_quiz(
        self,
        service: AttemptAnswerService,
    ):
        """Test that AccessDeniedException is raised for private quiz without access."""
        quiz_id = uuid.uuid4()
        service.quiz_read_port.get_quiz_access = AsyncMock(
            side_effect=QuizAccessDeniedException(
                "You do not have access to this quiz",
            ),
        )

        with pytest.raises(QuizAccessDeniedException):
            await service.start_or_resume_attempt(uuid.uuid4(), quiz_id)


class TestSaveAnswer:
    """Tests for save_answer method."""

    async def test_save_multiple_choice_answer(
        self,
        service: AttemptAnswerService,
        sample_attempt: Attempt,
        sample_task: MultipleChoiceTaskResponse,
    ):
        """Test saving a multiple choice answer."""
        sample_task.quiz_id = sample_attempt.quiz_id
        user_id = sample_attempt.user_id

        service.attempt_repo.get_by_id = AsyncMock(return_value=sample_attempt)
        service.quiz_read_port.get_task = AsyncMock(return_value=sample_task)

        answer = MagicMock()
        answer.answer_id = uuid.uuid4()
        service.answer_repo.upsert_multiple_choice = AsyncMock(return_value=answer)

        payload = MultipleChoiceAnswerUpsert(
            type="multiple_choice",
            data=MultipleChoiceAnswerData(selected_option_ids=[uuid.uuid4()]),
        )

        result = await service.save_answer(
            user_id,
            sample_attempt.attempt_id,
            sample_task.task_id,
            payload,
        )

        assert result.answer_id == answer.answer_id
        service.answer_repo.upsert_multiple_choice.assert_called_once()


class TestGetAttemptWithAnswers:
    """Tests for get_attempt_with_answers method."""

    async def test_get_attempt_with_answers_success(
        self,
        service: AttemptAnswerService,
        sample_attempt: Attempt,
    ):
        """Test fetching an attempt with answers."""
        user_id = sample_attempt.user_id
        task_id = uuid.uuid4()
        answer = FreeTextAnswer(
            attempt_id=sample_attempt.attempt_id,
            task_id=task_id,
            text_response="example answer",
        )

        service.attempt_repo.get_by_id = AsyncMock(return_value=sample_attempt)
        service.answer_repo.list_by_attempt = AsyncMock(return_value=[answer])

        result = await service.get_attempt_with_answers(
            user_id,
            sample_attempt.attempt_id,
        )

        assert result.attempt_id == sample_attempt.attempt_id
        assert result.answers[0].task_id == task_id

    async def test_get_attempt_with_answers_not_found(
        self,
        service: AttemptAnswerService,
    ):
        """Test attempt not found raises exception."""
        service.attempt_repo.get_by_id = AsyncMock(return_value=None)

        with pytest.raises(AttemptNotFoundException):
            await service.get_attempt_with_answers(uuid.uuid4(), uuid.uuid4())

    async def test_save_free_text_answer(
        self,
        service: AttemptAnswerService,
        sample_attempt: Attempt,
    ):
        """Test saving a free text answer."""
        task = FreeTextTaskResponse(
            task_id=uuid.uuid4(),
            quiz_id=sample_attempt.quiz_id,
            prompt="Prompt",
            topic_detail="Topic",
            order_index=0,
            type="free_text",
            reference_answer="Reference",
        )

        service.attempt_repo.get_by_id = AsyncMock(return_value=sample_attempt)
        service.quiz_read_port.get_task = AsyncMock(return_value=task)

        answer = MagicMock()
        answer.answer_id = uuid.uuid4()
        service.answer_repo.upsert_free_text = AsyncMock(return_value=answer)

        payload = FreeTextAnswerUpsert(
            type="free_text",
            data=FreeTextAnswerData(text_response="My answer"),
        )

        result = await service.save_answer(
            sample_attempt.user_id,
            sample_attempt.attempt_id,
            task.task_id,
            payload,
        )

        assert result.answer_id == answer.answer_id

    async def test_save_cloze_answer(
        self,
        service: AttemptAnswerService,
        sample_attempt: Attempt,
    ):
        """Test saving a cloze answer."""
        task = ClozeTaskResponse(
            task_id=uuid.uuid4(),
            quiz_id=sample_attempt.quiz_id,
            prompt="Prompt",
            topic_detail="Topic",
            order_index=0,
            type="cloze",
            template_text="Template",
            blanks=[],
        )

        service.attempt_repo.get_by_id = AsyncMock(return_value=sample_attempt)
        service.quiz_read_port.get_task = AsyncMock(return_value=task)

        answer = MagicMock()
        answer.answer_id = uuid.uuid4()
        service.answer_repo.upsert_cloze = AsyncMock(return_value=answer)

        payload = ClozeAnswerUpsert(
            type="cloze",
            data=ClozeAnswerData(
                provided_values=[
                    ClozeItemData(blank_id=uuid.uuid4(), value="answer"),
                ],
            ),
        )

        result = await service.save_answer(
            sample_attempt.user_id,
            sample_attempt.attempt_id,
            task.task_id,
            payload,
        )

        assert result.answer_id == answer.answer_id

    async def test_attempt_not_found_raises_exception(
        self,
        service: AttemptAnswerService,
    ):
        """Test that AttemptNotFoundException is raised when attempt doesn't exist."""
        service.attempt_repo.get_by_id = AsyncMock(return_value=None)

        payload = FreeTextAnswerUpsert(
            type="free_text",
            data=FreeTextAnswerData(text_response="test"),
        )

        with pytest.raises(AttemptNotFoundException):
            await service.save_answer(uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), payload)

    async def test_attempt_locked_raises_exception(
        self,
        service: AttemptAnswerService,
        sample_attempt: Attempt,
    ):
        """Test that AttemptLockedException is raised when attempt is evaluated."""
        sample_attempt.status = AttemptStatus.EVALUATED
        service.attempt_repo.get_by_id = AsyncMock(return_value=sample_attempt)

        payload = FreeTextAnswerUpsert(
            type="free_text",
            data=FreeTextAnswerData(text_response="test"),
        )

        with pytest.raises(AttemptLockedException):
            await service.save_answer(
                sample_attempt.user_id,
                sample_attempt.attempt_id,
                uuid.uuid4(),
                payload,
            )

    async def test_access_denied_wrong_user(
        self,
        service: AttemptAnswerService,
        sample_attempt: Attempt,
    ):
        """Test that AccessDeniedException is raised for wrong user."""
        service.attempt_repo.get_by_id = AsyncMock(return_value=sample_attempt)

        payload = FreeTextAnswerUpsert(
            type="free_text",
            data=FreeTextAnswerData(text_response="test"),
        )

        wrong_user_id = uuid.uuid4()
        with pytest.raises(AccessDeniedException):
            await service.save_answer(
                wrong_user_id,
                sample_attempt.attempt_id,
                uuid.uuid4(),
                payload,
            )

    async def test_task_not_found_raises_exception(
        self,
        service: AttemptAnswerService,
        sample_attempt: Attempt,
    ):
        """Test that TaskNotFoundException is raised when task doesn't exist."""
        service.attempt_repo.get_by_id = AsyncMock(return_value=sample_attempt)
        service.quiz_read_port.get_task = AsyncMock(
            side_effect=QuizModuleTaskNotFoundException(),
        )

        payload = FreeTextAnswerUpsert(
            type="free_text",
            data=FreeTextAnswerData(text_response="test"),
        )

        with pytest.raises(QuizModuleTaskNotFoundException):
            await service.save_answer(
                sample_attempt.user_id,
                sample_attempt.attempt_id,
                uuid.uuid4(),
                payload,
            )

    async def test_task_wrong_quiz_raises_exception(
        self,
        service: AttemptAnswerService,
        sample_attempt: Attempt,
    ):
        """Test that TaskNotFoundException is raised when task belongs to different quiz."""
        task = FreeTextTaskResponse(
            task_id=uuid.uuid4(),
            quiz_id=uuid.uuid4(),
            prompt="Prompt",
            topic_detail="Topic",
            order_index=0,
            type="free_text",
            reference_answer="Reference",
        )

        service.attempt_repo.get_by_id = AsyncMock(return_value=sample_attempt)
        service.quiz_read_port.get_task = AsyncMock(return_value=task)

        payload = FreeTextAnswerUpsert(
            type="free_text",
            data=FreeTextAnswerData(text_response="test"),
        )

        with pytest.raises(TaskNotFoundException):
            await service.save_answer(
                sample_attempt.user_id,
                sample_attempt.attempt_id,
                task.task_id,
                payload,
            )

    async def test_answer_type_mismatch_raises_exception(
        self,
        service: AttemptAnswerService,
        sample_attempt: Attempt,
        sample_task: MultipleChoiceTaskResponse,
    ):
        """Test that AnswerTypeMismatchException is raised for wrong answer type."""
        sample_task.quiz_id = sample_attempt.quiz_id

        service.attempt_repo.get_by_id = AsyncMock(return_value=sample_attempt)
        service.quiz_read_port.get_task = AsyncMock(return_value=sample_task)

        # Send free text answer for MC task
        payload = FreeTextAnswerUpsert(
            type="free_text",
            data=FreeTextAnswerData(text_response="test"),
        )

        with pytest.raises(AnswerTypeMismatchException):
            await service.save_answer(
                sample_attempt.user_id,
                sample_attempt.attempt_id,
                sample_task.task_id,
                payload,
            )


class TestSetFreeTextCorrectness:
    """Tests for set_free_text_correctness method."""

    async def test_set_correctness_true(
        self,
        service: AttemptAnswerService,
        sample_attempt: Attempt,
    ):
        """Test setting free text correctness to true."""
        answer = MagicMock(spec=FreeTextAnswer)
        answer.task_id = uuid.uuid4()

        service.attempt_repo.get_by_id = AsyncMock(return_value=sample_attempt)
        service.answer_repo.get_by_attempt_task = AsyncMock(return_value=answer)
        service.answer_repo.set_free_text_correctness = AsyncMock()

        await service.set_free_text_correctness(
            sample_attempt.user_id,
            sample_attempt.attempt_id,
            answer.task_id,
            True,
        )

        service.answer_repo.set_free_text_correctness.assert_called_once_with(
            sample_attempt.attempt_id,
            answer.task_id,
            True,
        )

    async def test_set_correctness_false(
        self,
        service: AttemptAnswerService,
        sample_attempt: Attempt,
    ):
        """Test setting free text correctness to false."""
        answer = MagicMock(spec=FreeTextAnswer)
        answer.task_id = uuid.uuid4()

        service.attempt_repo.get_by_id = AsyncMock(return_value=sample_attempt)
        service.answer_repo.get_by_attempt_task = AsyncMock(return_value=answer)
        service.answer_repo.set_free_text_correctness = AsyncMock()

        await service.set_free_text_correctness(
            sample_attempt.user_id,
            sample_attempt.attempt_id,
            answer.task_id,
            False,
        )

        service.answer_repo.set_free_text_correctness.assert_called_once_with(
            sample_attempt.attempt_id,
            answer.task_id,
            False,
        )


class TestListAttempts:
    """Tests for list_attempts method."""

    async def test_list_attempts_success(
        self,
        service: AttemptAnswerService,
    ):
        """Test listing attempts successfully."""
        user_id = uuid.uuid4()
        quiz_id = uuid.uuid4()

        # Create mock attempts
        attempt1 = MagicMock(spec=Attempt)
        attempt1.attempt_id = uuid.uuid4()
        attempt1.quiz_id = quiz_id
        attempt1.status = AttemptStatus.EVALUATED
        attempt1.started_at = datetime.now(timezone.utc)
        attempt1.evaluated_at = datetime.now(timezone.utc)
        attempt1.total_percentage = Decimal("85.00")

        attempt2 = MagicMock(spec=Attempt)
        attempt2.attempt_id = uuid.uuid4()
        attempt2.quiz_id = quiz_id
        attempt2.status = AttemptStatus.IN_PROGRESS
        attempt2.started_at = datetime.now(timezone.utc)
        attempt2.evaluated_at = None
        attempt2.total_percentage = None

        service.attempt_repo.list_by_user = AsyncMock(
            return_value=[attempt1, attempt2],
        )

        result = await service.list_attempts(user_id)

        assert len(result) == 2
        assert result[0].attempt_id == attempt1.attempt_id
        assert result[0].total_percentage == 85.00
        assert result[1].attempt_id == attempt2.attempt_id
        assert result[1].total_percentage is None
        service.attempt_repo.list_by_user.assert_called_once_with(user_id, None, None)

    async def test_list_attempts_with_quiz_filter(
        self,
        service: AttemptAnswerService,
    ):
        """Test listing attempts with quiz filter."""
        user_id = uuid.uuid4()
        quiz_id = uuid.uuid4()

        attempt = MagicMock(spec=Attempt)
        attempt.attempt_id = uuid.uuid4()
        attempt.quiz_id = quiz_id
        attempt.status = AttemptStatus.IN_PROGRESS
        attempt.started_at = datetime.now(timezone.utc)
        attempt.evaluated_at = None
        attempt.total_percentage = None

        service.attempt_repo.list_by_user = AsyncMock(return_value=[attempt])

        result = await service.list_attempts(user_id, quiz_id=quiz_id)

        assert len(result) == 1
        service.attempt_repo.list_by_user.assert_called_once_with(
            user_id,
            quiz_id,
            None,
        )

    async def test_list_attempts_with_status_filter(
        self,
        service: AttemptAnswerService,
    ):
        """Test listing attempts with status filter."""
        user_id = uuid.uuid4()

        attempt = MagicMock(spec=Attempt)
        attempt.attempt_id = uuid.uuid4()
        attempt.quiz_id = uuid.uuid4()
        attempt.status = AttemptStatus.EVALUATED
        attempt.started_at = datetime.now(timezone.utc)
        attempt.evaluated_at = datetime.now(timezone.utc)
        attempt.total_percentage = Decimal("90.00")

        service.attempt_repo.list_by_user = AsyncMock(return_value=[attempt])

        result = await service.list_attempts(user_id, status=AttemptStatus.EVALUATED)

        assert len(result) == 1
        service.attempt_repo.list_by_user.assert_called_once_with(
            user_id,
            None,
            AttemptStatus.EVALUATED,
        )

    async def test_list_attempts_empty(
        self,
        service: AttemptAnswerService,
    ):
        """Test listing attempts when none exist."""
        user_id = uuid.uuid4()

        service.attempt_repo.list_by_user = AsyncMock(return_value=[])

        result = await service.list_attempts(user_id)

        assert result == []
