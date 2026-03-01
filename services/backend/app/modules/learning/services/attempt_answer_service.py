"""Business logic for Attempt/Answer orchestration and authorization checks."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.learning.exceptions import (
    AttemptNotFoundException,
    AttemptLockedException,
    QuizNotCompletedException,
    AccessDeniedException,
    TaskNotFoundException,
    AnswerTypeMismatchException,
    AnswerNotFoundException,
    InvalidAnswerTypeException,
)
from app.modules.learning.models import AttemptStatus, FreeTextAnswer
from app.modules.learning.mappers import answer_to_dto
from app.modules.learning.repositories import AttemptRepository, AnswerRepository
from app.modules.learning.schemas import (
    AttemptListItem,
    AttemptDetailResponse,
    AttemptSummaryResponse,
    AnswerUpsertRequest,
    AnswerSavedResponse,
)
from app.modules.learning.strategies import AnswerMappingRegistry, AnswerUpsertRegistry
from app.shared.utils import quantize_percent
from app.shared.strategy_registry import StrategyNotFoundError

from app.shared.ports.quiz_read import QuizReadPort, TaskDetailView


def _validate_answer_type(
    payload: AnswerUpsertRequest,
    task: TaskDetailView,
) -> None:
    """
    Validate that answer type matches task type.

    Args:
        payload: Answer upsert request
        task: TaskDetailView instance

    Raises:
        AnswerTypeMismatchException: If types don't match
    """
    if task.type != payload.type:
        raise AnswerTypeMismatchException(task.type, payload.type)


class AttemptAnswerService:
    """Service for Attempt and Answer business logic."""

    def __init__(
        self,
        db: AsyncSession,
        quiz_read_port: QuizReadPort,
        upsert_registry: AnswerUpsertRegistry,
        mapping_registry: AnswerMappingRegistry,
        attempt_repo: AttemptRepository,
        answer_repo: AnswerRepository,
    ) -> None:
        """
        Initialize service with database session and repositories.

        Args:
            db: Async SQLAlchemy session
            quiz_read_port: Quiz read port instance
            upsert_registry: Strategy registry for answer upserts
            mapping_registry: Strategy registry for answer DTO mapping
            attempt_repo: AttemptRepository instance
            answer_repo: AnswerRepository instance
        """
        self.db = db
        self.attempt_repo = attempt_repo
        self.answer_repo = answer_repo
        self.quiz_read_port = quiz_read_port
        self.answer_upsert_registry = upsert_registry
        self.answer_mapping_registry = mapping_registry

    async def start_or_resume_attempt(
        self,
        user_id: UUID,
        quiz_id: UUID,
    ) -> tuple[AttemptSummaryResponse, bool]:
        """
        Start a new attempt or resume existing in_progress attempt.

        Args:
            user_id: UUID of the user
            quiz_id: UUID of the quiz

        Returns:
            Tuple of (AttemptSummaryResponse, is_new) where is_new=True means 201, False means 200

        Raises:
            QuizNotFoundException: If quiz not found
            QuizNotCompletedException: If quiz is not in COMPLETED status
            AccessDeniedException: If user has no access to quiz
        """
        # 1. Check quiz exists and user has access
        quiz_access = await self.quiz_read_port.get_quiz_access(
            quiz_id,
            user_id,
        )

        # 2. Check quiz status is COMPLETED
        status_value = getattr(quiz_access.status, "value", quiz_access.status)
        if status_value != "completed":
            raise QuizNotCompletedException(str(quiz_id))

        # 4. Check for existing open attempt
        existing = await self.attempt_repo.get_open_attempt(user_id, quiz_id)

        if existing:
            # Resume: load answers and return
            answers = await self.answer_repo.list_by_attempt(existing.attempt_id)
            existing_answers = [
                answer_to_dto(a, self.answer_mapping_registry) for a in answers
            ]
            return (
                AttemptSummaryResponse(
                    attempt_id=existing.attempt_id,
                    quiz_id=existing.quiz_id,
                    status=AttemptStatus(existing.status.value),
                    started_at=existing.started_at,
                    existing_answers=existing_answers,
                ),
                False,
            )

        # 5. Create new attempt
        attempt = await self.attempt_repo.create_attempt(user_id, quiz_id)
        await self.db.commit()

        return (
            AttemptSummaryResponse(
                attempt_id=attempt.attempt_id,
                quiz_id=attempt.quiz_id,
                status=AttemptStatus(attempt.status.value),
                started_at=attempt.started_at,
                existing_answers=[],
            ),
            True,
        )

    async def list_attempts(
        self,
        user_id: UUID,
        quiz_id: UUID | None = None,
        status: AttemptStatus | None = None,
    ) -> list[AttemptListItem]:
        """
        List all attempts for a user with optional filters.

        Args:
            user_id: UUID of the user
            quiz_id: Optional UUID to filter by quiz
            status: Optional status to filter by

        Returns:
            List of AttemptListItem ordered by started_at descending
        """
        attempts = await self.attempt_repo.list_by_user(user_id, quiz_id, status)

        return [
            AttemptListItem(
                attempt_id=a.attempt_id,
                quiz_id=a.quiz_id,
                status=AttemptStatus(a.status.value),
                started_at=a.started_at,
                evaluated_at=a.evaluated_at,
                total_percentage=(
                    float(quantize_percent(a.total_percentage))
                    if a.total_percentage is not None
                    else None
                ),
            )
            for a in attempts
        ]

    async def get_attempt_with_answers(
        self,
        user_id: UUID,
        attempt_id: UUID,
    ) -> AttemptDetailResponse:
        """
        Get a single attempt with its answers for the current user.

        Args:
            user_id: UUID of the user
            attempt_id: UUID of the attempt

        Returns:
            AttemptDetailResponse with attempt metadata and answers

        Raises:
            AttemptNotFoundException: If attempt not found
            AccessDeniedException: If user doesn't own the attempt
        """
        attempt = await self.attempt_repo.get_by_id(attempt_id)
        if not attempt:
            raise AttemptNotFoundException(str(attempt_id))

        if attempt.user_id != user_id:
            raise AccessDeniedException("Not your attempt")

        answers = await self.answer_repo.list_by_attempt(attempt_id)
        existing_answers = [
            answer_to_dto(a, self.answer_mapping_registry) for a in answers
        ]

        return AttemptDetailResponse(
            attempt_id=attempt.attempt_id,
            quiz_id=attempt.quiz_id,
            status=AttemptStatus(attempt.status.value),
            started_at=attempt.started_at,
            evaluated_at=attempt.evaluated_at,
            total_percentage=(
                float(quantize_percent(attempt.total_percentage))
                if attempt.total_percentage is not None
                else None
            ),
            answers=existing_answers,
        )

    async def save_answer(
        self,
        user_id: UUID,
        attempt_id: UUID,
        task_id: UUID,
        payload: AnswerUpsertRequest,
    ) -> AnswerSavedResponse:
        """
        Save/upsert an answer for a task in an attempt.

        Args:
            user_id: UUID of the user
            attempt_id: UUID of the attempt
            task_id: UUID of the task
            payload: Answer data (discriminated union)

        Returns:
            AnswerSavedResponse with answer_id and saved_at

        Raises:
            AttemptNotFoundException: If attempt not found
            AccessDeniedException: If user doesn't own the attempt
            AttemptLockedException: If attempt is already evaluated
            TaskNotFoundException: If task doesn't belong to quiz
            AnswerTypeMismatchException: If answer type doesn't match task type
        """
        # 1. Get attempt and verify ownership
        attempt = await self.attempt_repo.get_by_id(attempt_id)
        if not attempt:
            raise AttemptNotFoundException(str(attempt_id))

        if attempt.user_id != user_id:
            raise AccessDeniedException("Not your attempt")

        # 2. Check attempt is still in_progress
        if attempt.status != AttemptStatus.IN_PROGRESS:
            raise AttemptLockedException(str(attempt_id))

        # 3. Validate task belongs to quiz
        task = await self.quiz_read_port.get_task(task_id, user_id)
        if task.quiz_id != attempt.quiz_id:
            raise TaskNotFoundException(str(task_id))

        # 4. Validate answer type matches task type
        _validate_answer_type(payload, task)

        # 5. Upsert answer based on type
        try:
            strategy = self.answer_upsert_registry.get(payload.type)
            answer = await strategy.upsert(
                self.answer_repo,
                attempt_id,
                task_id,
                payload,
            )
        except (StrategyNotFoundError, ValueError) as exc:
            raise AnswerTypeMismatchException("unknown", payload.type) from exc

        await self.db.commit()

        return AnswerSavedResponse(
            answer_id=answer.answer_id,
            task_id=task_id,
            saved_at=datetime.now(timezone.utc),
        )

    async def set_free_text_correctness(
        self,
        user_id: UUID,
        attempt_id: UUID,
        task_id: UUID,
        is_correct: bool,
    ) -> None:
        """
        Set self-evaluation for free text answer (0% or 100%).

        Args:
            user_id: UUID of the user
            attempt_id: UUID of the attempt
            task_id: UUID of the task
            is_correct: Whether the answer is correct

        Raises:
            AttemptNotFoundException: If attempt not found
            AccessDeniedException: If user doesn't own the attempt
            AttemptLockedException: If attempt is already evaluated
            AnswerNotFoundException: If answer not found
            InvalidAnswerTypeException: If answer is not free_text
        """
        # 1. Get attempt and verify ownership
        attempt = await self.attempt_repo.get_by_id(attempt_id)
        if not attempt:
            raise AttemptNotFoundException(str(attempt_id))

        if attempt.user_id != user_id:
            raise AccessDeniedException("Not your attempt")

        # 2. Check attempt is still in_progress
        if attempt.status != AttemptStatus.IN_PROGRESS:
            raise AttemptLockedException(str(attempt_id))

        # 3. Get answer and verify it's free_text
        answer = await self.answer_repo.get_by_attempt_task(attempt_id, task_id)
        if not answer:
            raise AnswerNotFoundException(str(task_id))

        if not isinstance(answer, FreeTextAnswer):
            raise InvalidAnswerTypeException("free_text", answer.type.value)

        # 4. Set correctness
        await self.answer_repo.set_free_text_correctness(
            attempt_id,
            task_id,
            is_correct,
        )
        await self.db.commit()
