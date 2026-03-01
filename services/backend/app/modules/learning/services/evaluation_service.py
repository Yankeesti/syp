"""Evaluation service for business logic.

This module provides business logic orchestration for Attempt evaluation.
Service layer: coordinates repositories, handles evaluation logic, and orchestration.
"""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.learning.exceptions import (
    AttemptNotFoundException,
    AttemptLockedException,
    AccessDeniedException,
    InvalidAnswerTypeException,
)
from app.modules.learning.models import (
    AttemptStatus,
    Answer,
    AnswerType,
)
from app.modules.learning.repositories import AttemptRepository, AnswerRepository
from app.modules.learning.schemas import EvaluationResponse, AnswerDetailDTO
from app.modules.learning.schemas.evaluation import (
    MultipleChoiceAnswerDetail,
    FreeTextAnswerDetail,
    ClozeAnswerDetail,
)
from app.modules.learning.services.evaluation_strategies import (
    AnswerEvaluationRegistry,
    normalize_answer_type,
)
from app.shared.strategy_registry import StrategyNotFoundError
from app.shared.utils import quantize_percent

from app.shared.ports.quiz_read import QuizReadPort, TaskDetailView


class EvaluationService:
    """Service for Attempt evaluation business logic."""

    def __init__(
        self,
        db: AsyncSession,
        quiz_read_port: QuizReadPort,
        evaluation_registry: AnswerEvaluationRegistry,
        attempt_repo: AttemptRepository,
        answer_repo: AnswerRepository,
    ) -> None:
        """
        Initialize service with database session and repositories.

        Args:
            db: Async SQLAlchemy session
            quiz_read_port: Quiz read port instance
            evaluation_registry: Strategy registry for answer evaluation
            attempt_repo: AttemptRepository instance
            answer_repo: AnswerRepository instance
        """
        self.db = db
        self.attempt_repo = attempt_repo
        self.answer_repo = answer_repo
        self.quiz_read_port = quiz_read_port
        self.evaluation_registry = evaluation_registry

    async def evaluate_attempt(
        self,
        user_id: UUID,
        attempt_id: UUID,
    ) -> EvaluationResponse:
        """
        Evaluate all answers, calculate total percentage, lock attempt.

        Args:
            user_id: UUID of the user
            attempt_id: UUID of the attempt

        Returns:
            EvaluationResponse with total percentage and answer details

        Raises:
            AttemptNotFoundException: If attempt not found
            AccessDeniedException: If user doesn't own the attempt
            AttemptLockedException: If attempt is already evaluated
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

        # 3. Load all tasks for the quiz
        tasks = await self.quiz_read_port.get_tasks(
            attempt.quiz_id,
            user_id,
        )
        task_map = {t.task_id: t for t in tasks}

        # 4. Load all answers
        answers = await self.answer_repo.list_by_attempt(attempt_id)
        answer_map = {a.task_id: a for a in answers}

        # 5. Evaluate each task
        answer_details: list[AnswerDetailDTO] = []
        total_score = Decimal("0.0")

        for task in tasks:
            answer = answer_map.get(task.task_id)

            if answer is None:
                # No answer = 0%
                percentage = Decimal("0.0")
            else:
                # Evaluate based on type
                percentage = await self._evaluate_answer(answer, task)
                # Persist percentage on answer
                await self.answer_repo.set_answer_percentage(
                    answer.answer_id,
                    percentage,
                )

            total_score += percentage

            # Create detail DTO
            detail = self._create_answer_detail(task, percentage)
            answer_details.append(detail)

        # 6. Calculate total percentage
        if len(tasks) > 0:
            total_percentage = total_score / len(tasks)
        else:
            total_percentage = Decimal("0.0")

        # 7. Quantize and mark attempt as evaluated
        evaluated_at = datetime.now(timezone.utc)
        total_percentage = quantize_percent(total_percentage) or Decimal("0.00")
        await self.attempt_repo.mark_evaluated(
            attempt_id,
            total_percentage,
            evaluated_at,
        )
        await self.db.commit()

        return EvaluationResponse(
            attempt_id=attempt_id,
            quiz_id=attempt.quiz_id,
            total_percentage=total_percentage,
            evaluated_at=evaluated_at,
            answer_details=answer_details,
        )

    async def _evaluate_answer(
        self,
        answer: Answer,
        task: TaskDetailView,
    ) -> Decimal:
        """
        Evaluate single answer based on type.

        Args:
            answer: Answer instance (polymorphic)
            task: TaskDetailView instance (polymorphic)

        Returns:
            Percentage correct (0-100) as Decimal
        """
        try:
            strategy = self.evaluation_registry.get(
                normalize_answer_type(answer.type),
            )
            return await strategy.evaluate(answer, task, self.answer_repo)
        except StrategyNotFoundError as exc:
            expected_types = ", ".join(answer_type.value for answer_type in AnswerType)
            raise InvalidAnswerTypeException(
                expected_types,
                str(answer.type),
            ) from exc

    def _create_answer_detail(
        self,
        task: TaskDetailView,
        percentage: Decimal,
    ) -> AnswerDetailDTO:
        """
        Create AnswerDetailDTO based on task type.

        Args:
            task: TaskDetailView instance
            percentage: Percentage correct for this task

        Returns:
            AnswerDetailDTO (discriminated union)
        """
        if task.type == "multiple_choice":
            return MultipleChoiceAnswerDetail(
                task_id=task.task_id,
                type="multiple_choice",
                percentage_correct=quantize_percent(percentage) or Decimal("0.00"),
            )
        elif task.type == "free_text":
            return FreeTextAnswerDetail(
                task_id=task.task_id,
                type="free_text",
                percentage_correct=quantize_percent(percentage) or Decimal("0.00"),
            )
        elif task.type == "cloze":
            return ClozeAnswerDetail(
                task_id=task.task_id,
                type="cloze",
                percentage_correct=quantize_percent(percentage) or Decimal("0.00"),
            )
        else:  # ToDo: throw exception no fallback to MultipleChoice AnswerDetail!!!
            # Fallback
            return MultipleChoiceAnswerDetail(
                task_id=task.task_id,
                type="multiple_choice",
                percentage_correct=quantize_percent(percentage) or Decimal("0.00"),
            )
