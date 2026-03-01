"""Tests for EvaluationService."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.learning.exceptions import (
    AttemptNotFoundException,
    AttemptLockedException,
    AccessDeniedException,
)
from app.modules.learning.models import (
    Attempt,
    AttemptStatus,
    AnswerType,
    MultipleChoiceAnswer,
    FreeTextAnswer,
    ClozeAnswer,
    AnswerClozeItem,
)
from app.modules.learning.repositories import AttemptRepository, AnswerRepository
from app.modules.learning.services import EvaluationService
from app.modules.learning.services.evaluation_strategies import (
    AnswerEvaluationRegistry,
    answer_evaluation_registry,
)
from app.shared.ports.quiz_read import QuizReadPort
from app.modules.quiz.schemas import (
    MultipleChoiceOptionResponse,
    MultipleChoiceTaskResponse,
    FreeTextTaskResponse,
    ClozeBlankResponse,
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
    repo = MagicMock(spec=AnswerRepository)
    repo.set_cloze_item_correct = AsyncMock()
    return repo


@pytest.fixture
def service(
    mock_db_session: AsyncMock,
    mock_quiz_read_port: MagicMock,
    evaluation_registry: AnswerEvaluationRegistry,
    mock_attempt_repo: MagicMock,
    mock_answer_repo: MagicMock,
) -> EvaluationService:
    """Create service with mocked dependencies."""
    return EvaluationService(
        mock_db_session,
        mock_quiz_read_port,
        evaluation_registry,
        mock_attempt_repo,
        mock_answer_repo,
    )


@pytest.fixture
def evaluation_registry() -> AnswerEvaluationRegistry:
    """Create evaluation registry with mocked repository."""
    return answer_evaluation_registry()


@pytest.fixture
def sample_attempt() -> Attempt:
    """Create a sample in-progress attempt."""
    attempt = MagicMock(spec=Attempt)
    attempt.attempt_id = uuid.uuid4()
    attempt.quiz_id = uuid.uuid4()
    attempt.user_id = uuid.uuid4()
    attempt.status = AttemptStatus.IN_PROGRESS
    return attempt


class TestEvaluateAttempt:
    """Tests for evaluate_attempt method."""

    async def test_evaluate_with_no_tasks(
        self,
        service: EvaluationService,
        sample_attempt: Attempt,
    ):
        """Test evaluation when quiz has no tasks."""
        service.attempt_repo.get_by_id = AsyncMock(return_value=sample_attempt)
        service.quiz_read_port.get_tasks = AsyncMock(return_value=[])
        service.answer_repo.list_by_attempt = AsyncMock(return_value=[])
        service.attempt_repo.mark_evaluated = AsyncMock()

        result = await service.evaluate_attempt(
            sample_attempt.user_id,
            sample_attempt.attempt_id,
        )

        assert result.total_percentage == Decimal("0.0")
        assert len(result.answer_details) == 0

    async def test_evaluate_multiple_choice_correct(
        self,
        service: EvaluationService,
        sample_attempt: Attempt,
    ):
        """Test evaluation of correct multiple choice answer."""
        correct_option_id = uuid.uuid4()

        # Create MC task with correct option
        task = MultipleChoiceTaskResponse(
            task_id=uuid.uuid4(),
            quiz_id=sample_attempt.quiz_id,
            prompt="Prompt",
            topic_detail="Topic",
            order_index=0,
            type="multiple_choice",
            options=[
                MultipleChoiceOptionResponse(
                    option_id=correct_option_id,
                    text="Option",
                    is_correct=True,
                    explanation=None,
                ),
            ],
        )

        # Create MC answer with correct selection
        answer = MagicMock(spec=MultipleChoiceAnswer)
        answer.answer_id = uuid.uuid4()
        answer.task_id = task.task_id
        answer.type = AnswerType.MULTIPLE_CHOICE
        selection = MagicMock()
        selection.option_id = correct_option_id
        answer.selections = [selection]

        service.attempt_repo.get_by_id = AsyncMock(return_value=sample_attempt)
        service.quiz_read_port.get_tasks = AsyncMock(return_value=[task])
        service.answer_repo.list_by_attempt = AsyncMock(return_value=[answer])
        service.answer_repo.set_answer_percentage = AsyncMock()
        service.attempt_repo.mark_evaluated = AsyncMock()

        result = await service.evaluate_attempt(
            sample_attempt.user_id,
            sample_attempt.attempt_id,
        )

        assert result.total_percentage == Decimal("100.0")
        assert result.answer_details[0].percentage_correct == Decimal("100.0")

    async def test_evaluate_multiple_choice_incorrect(
        self,
        service: EvaluationService,
        sample_attempt: Attempt,
    ):
        """Test evaluation of incorrect multiple choice answer."""
        correct_option_id = uuid.uuid4()
        wrong_option_id = uuid.uuid4()

        task = MultipleChoiceTaskResponse(
            task_id=uuid.uuid4(),
            quiz_id=sample_attempt.quiz_id,
            prompt="Prompt",
            topic_detail="Topic",
            order_index=0,
            type="multiple_choice",
            options=[
                MultipleChoiceOptionResponse(
                    option_id=correct_option_id,
                    text="Option",
                    is_correct=True,
                    explanation=None,
                ),
            ],
        )

        answer = MagicMock(spec=MultipleChoiceAnswer)
        answer.answer_id = uuid.uuid4()
        answer.task_id = task.task_id
        answer.type = AnswerType.MULTIPLE_CHOICE
        selection = MagicMock()
        selection.option_id = wrong_option_id  # Wrong selection
        answer.selections = [selection]

        service.attempt_repo.get_by_id = AsyncMock(return_value=sample_attempt)
        service.quiz_read_port.get_tasks = AsyncMock(return_value=[task])
        service.answer_repo.list_by_attempt = AsyncMock(return_value=[answer])
        service.answer_repo.set_answer_percentage = AsyncMock()
        service.attempt_repo.mark_evaluated = AsyncMock()

        result = await service.evaluate_attempt(
            sample_attempt.user_id,
            sample_attempt.attempt_id,
        )

        assert result.total_percentage == Decimal("0.0")

    async def test_evaluate_free_text_with_correctness_set(
        self,
        service: EvaluationService,
        sample_attempt: Attempt,
    ):
        """Test evaluation of free text answer with pre-set correctness."""
        task = FreeTextTaskResponse(
            task_id=uuid.uuid4(),
            quiz_id=sample_attempt.quiz_id,
            prompt="Prompt",
            topic_detail="Topic",
            order_index=0,
            type="free_text",
            reference_answer="Reference",
        )

        answer = MagicMock(spec=FreeTextAnswer)
        answer.answer_id = uuid.uuid4()
        answer.task_id = task.task_id
        answer.type = AnswerType.FREE_TEXT
        answer.percentage_correct = Decimal("100.0")  # Pre-set via PATCH

        service.attempt_repo.get_by_id = AsyncMock(return_value=sample_attempt)
        service.quiz_read_port.get_tasks = AsyncMock(return_value=[task])
        service.answer_repo.list_by_attempt = AsyncMock(return_value=[answer])
        service.answer_repo.set_answer_percentage = AsyncMock()
        service.attempt_repo.mark_evaluated = AsyncMock()

        result = await service.evaluate_attempt(
            sample_attempt.user_id,
            sample_attempt.attempt_id,
        )

        assert result.total_percentage == Decimal("100.0")

    async def test_evaluate_free_text_without_correctness(
        self,
        service: EvaluationService,
        sample_attempt: Attempt,
    ):
        """Test evaluation of free text answer without pre-set correctness (defaults to 0)."""
        task = FreeTextTaskResponse(
            task_id=uuid.uuid4(),
            quiz_id=sample_attempt.quiz_id,
            prompt="Prompt",
            topic_detail="Topic",
            order_index=0,
            type="free_text",
            reference_answer="Reference",
        )

        answer = MagicMock(spec=FreeTextAnswer)
        answer.answer_id = uuid.uuid4()
        answer.task_id = task.task_id
        answer.type = AnswerType.FREE_TEXT
        answer.percentage_correct = None  # Not set

        service.attempt_repo.get_by_id = AsyncMock(return_value=sample_attempt)
        service.quiz_read_port.get_tasks = AsyncMock(return_value=[task])
        service.answer_repo.list_by_attempt = AsyncMock(return_value=[answer])
        service.answer_repo.set_answer_percentage = AsyncMock()
        service.attempt_repo.mark_evaluated = AsyncMock()

        result = await service.evaluate_attempt(
            sample_attempt.user_id,
            sample_attempt.attempt_id,
        )

        assert result.total_percentage == Decimal("0.0")

    async def test_evaluate_cloze_all_correct(
        self,
        service: EvaluationService,
        sample_attempt: Attempt,
    ):
        """Test evaluation of cloze answer with all blanks correct."""
        blank1_id = uuid.uuid4()
        blank2_id = uuid.uuid4()

        task = ClozeTaskResponse(
            task_id=uuid.uuid4(),
            quiz_id=sample_attempt.quiz_id,
            prompt="Prompt",
            topic_detail="Topic",
            order_index=0,
            type="cloze",
            template_text="Template",
            blanks=[
                ClozeBlankResponse(
                    blank_id=blank1_id,
                    position=0,
                    expected_value="answer1",
                ),
                ClozeBlankResponse(
                    blank_id=blank2_id,
                    position=1,
                    expected_value="answer2",
                ),
            ],
        )

        answer = MagicMock(spec=ClozeAnswer)
        answer.answer_id = uuid.uuid4()
        answer.task_id = task.task_id
        answer.type = AnswerType.CLOZE
        item1 = MagicMock(spec=AnswerClozeItem)
        item1.blank_id = blank1_id
        item1.provided_value = "answer1"
        item2 = MagicMock(spec=AnswerClozeItem)
        item2.blank_id = blank2_id
        item2.provided_value = "answer2"
        answer.items = [item1, item2]

        service.attempt_repo.get_by_id = AsyncMock(return_value=sample_attempt)
        service.quiz_read_port.get_tasks = AsyncMock(return_value=[task])
        service.answer_repo.list_by_attempt = AsyncMock(return_value=[answer])
        service.answer_repo.set_answer_percentage = AsyncMock()
        service.answer_repo.set_cloze_item_correct = AsyncMock()
        service.attempt_repo.mark_evaluated = AsyncMock()

        result = await service.evaluate_attempt(
            sample_attempt.user_id,
            sample_attempt.attempt_id,
        )

        assert result.total_percentage == Decimal("100.0")

    async def test_evaluate_cloze_partial_correct(
        self,
        service: EvaluationService,
        sample_attempt: Attempt,
    ):
        """Test evaluation of cloze answer with partial correct blanks."""
        blank1_id = uuid.uuid4()
        blank2_id = uuid.uuid4()

        task = ClozeTaskResponse(
            task_id=uuid.uuid4(),
            quiz_id=sample_attempt.quiz_id,
            prompt="Prompt",
            topic_detail="Topic",
            order_index=0,
            type="cloze",
            template_text="Template",
            blanks=[
                ClozeBlankResponse(
                    blank_id=blank1_id,
                    position=0,
                    expected_value="correct",
                ),
                ClozeBlankResponse(
                    blank_id=blank2_id,
                    position=1,
                    expected_value="expected",
                ),
            ],
        )

        answer = MagicMock(spec=ClozeAnswer)
        answer.answer_id = uuid.uuid4()
        answer.task_id = task.task_id
        answer.type = AnswerType.CLOZE
        item1 = MagicMock(spec=AnswerClozeItem)
        item1.blank_id = blank1_id
        item1.provided_value = "correct"  # Correct
        item2 = MagicMock(spec=AnswerClozeItem)
        item2.blank_id = blank2_id
        item2.provided_value = "wrong"  # Wrong
        answer.items = [item1, item2]

        service.attempt_repo.get_by_id = AsyncMock(return_value=sample_attempt)
        service.quiz_read_port.get_tasks = AsyncMock(return_value=[task])
        service.answer_repo.list_by_attempt = AsyncMock(return_value=[answer])
        service.answer_repo.set_answer_percentage = AsyncMock()
        service.answer_repo.set_cloze_item_correct = AsyncMock()
        service.attempt_repo.mark_evaluated = AsyncMock()

        result = await service.evaluate_attempt(
            sample_attempt.user_id,
            sample_attempt.attempt_id,
        )

        assert result.total_percentage == Decimal("50.0")

    async def test_evaluate_cloze_with_regex(
        self,
        service: EvaluationService,
        sample_attempt: Attempt,
    ):
        """Test evaluation of cloze answer with regex pattern."""
        blank_id = uuid.uuid4()

        task = ClozeTaskResponse(
            task_id=uuid.uuid4(),
            quiz_id=sample_attempt.quiz_id,
            prompt="Prompt",
            topic_detail="Topic",
            order_index=0,
            type="cloze",
            template_text="Template",
            blanks=[
                ClozeBlankResponse(
                    blank_id=blank_id,
                    position=0,
                    expected_value=r"\d{4}",
                ),
            ],
        )

        answer = MagicMock(spec=ClozeAnswer)
        answer.answer_id = uuid.uuid4()
        answer.task_id = task.task_id
        answer.type = AnswerType.CLOZE
        item = MagicMock(spec=AnswerClozeItem)
        item.blank_id = blank_id
        item.provided_value = "2024"  # Matches regex
        answer.items = [item]

        service.attempt_repo.get_by_id = AsyncMock(return_value=sample_attempt)
        service.quiz_read_port.get_tasks = AsyncMock(return_value=[task])
        service.answer_repo.list_by_attempt = AsyncMock(return_value=[answer])
        service.answer_repo.set_answer_percentage = AsyncMock()
        service.answer_repo.set_cloze_item_correct = AsyncMock()
        service.attempt_repo.mark_evaluated = AsyncMock()

        result = await service.evaluate_attempt(
            sample_attempt.user_id,
            sample_attempt.attempt_id,
        )

        assert result.total_percentage == Decimal("100.0")

    async def test_evaluate_missing_answer_counts_as_zero(
        self,
        service: EvaluationService,
        sample_attempt: Attempt,
    ):
        """Test that missing answers count as 0%."""
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
        service.quiz_read_port.get_tasks = AsyncMock(return_value=[task])
        service.answer_repo.list_by_attempt = AsyncMock(return_value=[])  # No answers
        service.attempt_repo.mark_evaluated = AsyncMock()

        result = await service.evaluate_attempt(
            sample_attempt.user_id,
            sample_attempt.attempt_id,
        )

        assert result.total_percentage == Decimal("0.0")
        assert result.answer_details[0].percentage_correct == Decimal("0.0")

    async def test_evaluate_average_calculation(
        self,
        service: EvaluationService,
        sample_attempt: Attempt,
    ):
        """Test that total percentage is average of all tasks."""
        task1 = FreeTextTaskResponse(
            task_id=uuid.uuid4(),
            quiz_id=sample_attempt.quiz_id,
            prompt="Prompt",
            topic_detail="Topic",
            order_index=0,
            type="free_text",
            reference_answer="Reference",
        )

        task2 = FreeTextTaskResponse(
            task_id=uuid.uuid4(),
            quiz_id=sample_attempt.quiz_id,
            prompt="Prompt",
            topic_detail="Topic",
            order_index=1,
            type="free_text",
            reference_answer="Reference",
        )

        answer1 = MagicMock(spec=FreeTextAnswer)
        answer1.answer_id = uuid.uuid4()
        answer1.task_id = task1.task_id
        answer1.type = AnswerType.FREE_TEXT
        answer1.percentage_correct = Decimal("100.0")

        answer2 = MagicMock(spec=FreeTextAnswer)
        answer2.answer_id = uuid.uuid4()
        answer2.task_id = task2.task_id
        answer2.type = AnswerType.FREE_TEXT
        answer2.percentage_correct = Decimal("0.0")

        service.attempt_repo.get_by_id = AsyncMock(return_value=sample_attempt)
        service.quiz_read_port.get_tasks = AsyncMock(return_value=[task1, task2])
        service.answer_repo.list_by_attempt = AsyncMock(return_value=[answer1, answer2])
        service.answer_repo.set_answer_percentage = AsyncMock()
        service.attempt_repo.mark_evaluated = AsyncMock()

        result = await service.evaluate_attempt(
            sample_attempt.user_id,
            sample_attempt.attempt_id,
        )

        assert result.total_percentage == Decimal("50.0")

    async def test_attempt_not_found_raises_exception(
        self,
        service: EvaluationService,
    ):
        """Test that AttemptNotFoundException is raised when attempt doesn't exist."""
        service.attempt_repo.get_by_id = AsyncMock(return_value=None)

        with pytest.raises(AttemptNotFoundException):
            await service.evaluate_attempt(uuid.uuid4(), uuid.uuid4())

    async def test_attempt_locked_raises_exception(
        self,
        service: EvaluationService,
        sample_attempt: Attempt,
    ):
        """Test that AttemptLockedException is raised when already evaluated."""
        sample_attempt.status = AttemptStatus.EVALUATED
        service.attempt_repo.get_by_id = AsyncMock(return_value=sample_attempt)

        with pytest.raises(AttemptLockedException):
            await service.evaluate_attempt(
                sample_attempt.user_id,
                sample_attempt.attempt_id,
            )

    async def test_access_denied_wrong_user(
        self,
        service: EvaluationService,
        sample_attempt: Attempt,
    ):
        """Test that AccessDeniedException is raised for wrong user."""
        service.attempt_repo.get_by_id = AsyncMock(return_value=sample_attempt)

        wrong_user_id = uuid.uuid4()
        with pytest.raises(AccessDeniedException):
            await service.evaluate_attempt(wrong_user_id, sample_attempt.attempt_id)
