"""Quiz service for business logic.

This module provides business logic orchestration for Quiz entities.
Service layer: coordinates repositories, handles authorization, and orchestration.
"""

import logging
import uuid

from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import sessionmanager
from app.modules.quiz.repositories.quiz_repository import QuizRepository
from app.modules.quiz.repositories.quiz_ownership_repository import (
    QuizOwnershipRepository,
)
from app.modules.quiz.repositories.task_repository import TaskRepository
from app.modules.quiz.repositories.quiz_version_repository import QuizVersionRepository
from app.modules.quiz.models import Quiz, QuizStatus, QuizState, OwnershipRole, Task
from app.modules.quiz.models.task import TaskType
from app.modules.quiz.schemas.quiz_output import (
    QuizCreationStatus,
    QuizDetailDto,
    QuizSummaryDto,
)
from app.modules.quiz.schemas import QuizAccessDto, QuizGenerationSpec, TaskDetailDto
from app.modules.quiz.mappers import quiz_to_detail_response, quiz_to_list_item
from app.modules.quiz.exceptions import (
    QuizNotFoundException,
    TaskNotFoundException,
    AccessDeniedException,
)
from app.modules.quiz.constants import QUIZ_TITLE_PENDING
from app.modules.quiz.strategies import (
    TaskMappingRegistry,
    normalize_task_type,
)
from app.shared.ports.quiz_events import QuizDeletedEvent, QuizEventPublisher
from app.shared.ports.quiz_generation import QuizGenerationPort

logger = logging.getLogger(__name__)


class QuizService:
    """Service for Quiz business logic."""

    def __init__(
        self,
        db: AsyncSession,
        quiz_repo: QuizRepository,
        ownership_repo: QuizOwnershipRepository,
        task_repo: TaskRepository,
        version_repo: QuizVersionRepository,
        mapping_registry: TaskMappingRegistry,
        event_publisher: QuizEventPublisher,
        generation_port: QuizGenerationPort,
    ):
        """
        Initialize service with database session and repositories.

        Args:
            db: Async SQLAlchemy session
            quiz_repo: Quiz repository instance
            ownership_repo: Quiz ownership repository instance
            task_repo: Task repository instance
            version_repo: Quiz version repository instance
            mapping_registry: Task mapping registry
            event_publisher: Quiz event publisher
            generation_port: Quiz generation port
        """
        self.db = db
        self.quiz_repo = quiz_repo
        self.ownership_repo = ownership_repo
        self.task_repo = task_repo
        self.version_repo = version_repo
        self.task_mapping_registry = mapping_registry
        self.event_publisher = event_publisher
        self.generation_port = generation_port

    async def list_user_quizzes(
        self,
        user_id: uuid.UUID,
        roles: list[OwnershipRole] | None = None,
    ) -> list[QuizSummaryDto]:
        """
        List all quizzes where the user has ownership.

        Args:
            user_id: UUID of the user
            roles: Optional list of roles to filter by (None = all roles)

        Returns:
            List of QuizSummaryDtos with role information
        """
        quiz_role_tuples = await self.ownership_repo.get_quizzes_by_user(
            user_id,
            roles,
        )

        quiz_ids = [quiz.quiz_id for quiz, _ in quiz_role_tuples]
        task_counts: dict[uuid.UUID, int] = {quiz_id: 0 for quiz_id in quiz_ids}
        task_types: dict[uuid.UUID, set[TaskType]] = {
            quiz_id: set() for quiz_id in quiz_ids
        }

        if quiz_ids:
            task_rows = await self.task_repo.list_types_by_quiz_ids(quiz_ids)
            for quiz_id, task_type in task_rows:
                task_counts[quiz_id] = task_counts.get(quiz_id, 0) + 1
                if isinstance(task_type, TaskType):
                    task_types.setdefault(quiz_id, set()).add(task_type)

        return [
            quiz_to_list_item(
                quiz,
                role,
                question_count=task_counts.get(quiz.quiz_id, 0),
                question_types=sorted(
                    task_types.get(quiz.quiz_id, set()),
                    key=lambda value: value.value,
                ),
            )
            for quiz, role in quiz_role_tuples
        ]

    async def create_quiz(
        self,
        background_tasks: BackgroundTasks,
        user_id: uuid.UUID,
        generation_input: QuizGenerationSpec,
    ) -> QuizCreationStatus:
        """
        Create a new quiz and start background generation.

        Creates quiz with PENDING status and schedules LLM generation
        as a background task.

        Args:
            background_tasks: FastAPI BackgroundTasks for async generation
            user_id: UUID of the user creating the quiz
            generation_input: Input for LLM generation (task_types, description, file)

        Returns:
            QuizCreationStatus with quiz_id and status (202 Accepted pattern)
        """
        # Create quiz with placeholder title (will be updated by LLM)
        quiz = await self.quiz_repo.create(
            title=QUIZ_TITLE_PENDING,
            created_by=user_id,
            topic=generation_input.user_description or "",
            status=QuizStatus.PENDING,
        )

        initial_version = await self.version_repo.create_published(
            quiz_id=quiz.quiz_id,
            created_by=user_id,
            version_number=1,
            is_current=True,
        )

        await self.ownership_repo.create(
            quiz_id=quiz.quiz_id,
            user_id=user_id,
            role=OwnershipRole.OWNER,
        )

        await self.db.commit()

        # Schedule background task for LLM generation
        background_tasks.add_task(
            generate_quiz_content,
            quiz_id=quiz.quiz_id,
            quiz_version_id=initial_version.quiz_version_id,
            generation_input=generation_input,
            generation_port=self.generation_port,
            mapping_registry=self.task_mapping_registry,
        )

        return QuizCreationStatus(quiz_id=quiz.quiz_id, status=quiz.status)

    async def get_quiz_detail(
        self,
        quiz_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> QuizDetailDto:
        """
        Get detailed quiz information with tasks.

        Args:
            quiz_id: UUID of the quiz
            user_id: UUID of the user requesting the quiz

        Returns:
            QuizDetailDto with quiz details and tasks

        Raises:
            AccessDeniedException: If user has no access
            QuizNotFoundException: If quiz not found
        """
        quiz = await self._get_quiz_or_raise(quiz_id)
        await self._ensure_quiz_access(quiz, user_id)

        current_version_id = await self.version_repo.get_current_version_id(quiz_id)
        if current_version_id is None:
            raise QuizNotFoundException("Quiz version not initialized")

        tasks = await self.task_repo.get_by_quiz_version(current_version_id)
        task_dtos = [self._task_to_dto(task) for task in tasks]

        return quiz_to_detail_response(quiz, task_dtos)

    async def get_quiz_access(
        self,
        quiz_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> QuizAccessDto:
        """
        Get access-checked quiz metadata for other modules.

        Args:
            quiz_id: UUID of the quiz
            user_id: UUID of the requesting user

        Returns:
            QuizAccessDto with quiz status and state
        """
        quiz = await self._get_quiz_or_raise(quiz_id)
        await self._ensure_quiz_access(quiz, user_id)

        return QuizAccessDto(
            quiz_id=quiz.quiz_id,
            status=quiz.status,
            state=quiz.state,
        )

    async def get_tasks(
        self,
        quiz_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> list[TaskDetailDto]:
        """
        Get access-checked tasks for a quiz.

        Args:
            quiz_id: UUID of the quiz
            user_id: UUID of the requesting user

        Returns:
            List of TaskDetailDto for the quiz
        """
        quiz = await self._get_quiz_or_raise(quiz_id)
        await self._ensure_quiz_access(quiz, user_id)

        current_version_id = await self.version_repo.get_current_version_id(quiz_id)
        if current_version_id is None:
            raise QuizNotFoundException("Quiz version not initialized")

        tasks = await self.task_repo.get_by_quiz_version(current_version_id)
        return [self._task_to_dto(task) for task in tasks]

    async def get_task(
        self,
        task_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> TaskDetailDto:
        """
        Get access-checked task by ID.

        Args:
            task_id: UUID of the task
            user_id: UUID of the requesting user

        Returns:
            TaskDetailDto for the task
        """
        task = await self.task_repo.get_by_id(task_id)
        if task is None:
            raise TaskNotFoundException()

        quiz = await self._get_quiz_or_raise(task.quiz_id)
        await self._ensure_quiz_access(quiz, user_id)

        return self._task_to_dto(task)

    def _task_to_dto(self, task: Task) -> TaskDetailDto:
        task_type = normalize_task_type(task.type)
        return self.task_mapping_registry.get(task_type).to_dto(task)

    async def _get_quiz_or_raise(self, quiz_id: uuid.UUID) -> Quiz:
        quiz = await self.quiz_repo.get_by_id(quiz_id, load_tasks=False)
        if quiz is None:
            raise QuizNotFoundException()
        return quiz

    async def _ensure_quiz_access(self, quiz: Quiz, user_id: uuid.UUID) -> None:
        if quiz.state == QuizState.PUBLIC:
            return

        has_access = await self.ownership_repo.user_has_access(
            quiz_id=quiz.quiz_id,
            user_id=user_id,
        )
        if not has_access:
            raise AccessDeniedException("You do not have access to this quiz")

    async def delete_quiz(
        self,
        quiz_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        """
        Delete a quiz.

        Only the quiz owner can delete the quiz. Cascades to tasks and ownerships.
        Also publishes a quiz deletion event for cleanup in other modules.

        Args:
            quiz_id: UUID of the quiz to delete
            user_id: UUID of the user requesting deletion

        Raises:
            AccessDeniedException: If user is not owner
            QuizNotFoundException: If quiz not found
        """
        has_owner_access = await self.ownership_repo.user_has_access(
            quiz_id=quiz_id,
            user_id=user_id,
            required_role=OwnershipRole.OWNER,
        )

        if not has_owner_access:
            raise AccessDeniedException("Only the quiz owner can delete the quiz")

        deleted = await self.quiz_repo.delete(quiz_id)

        if not deleted:
            raise QuizNotFoundException()

        await self.event_publisher.publish_quiz_deleted(
            QuizDeletedEvent(quiz_id=quiz_id, db=self.db),
        )

        await self.db.commit()


async def generate_quiz_content(
    quiz_id: uuid.UUID,
    quiz_version_id: uuid.UUID,
    generation_input: QuizGenerationSpec,
    generation_port: QuizGenerationPort,
    mapping_registry: TaskMappingRegistry,
) -> None:
    """
    Background task for LLM-based quiz generation.

    This function runs in a background task after the HTTP response is sent.
    It creates its own database sessions to avoid issues with closed connections.

    Flow:
    1. Update status to GENERATING (short DB session)
    2. Call LLM to generate quiz content (no DB session - may be slow)
    3. Persist generated content (new DB session)
    4. Update status to COMPLETED or FAILED

    Args:
        quiz_id: UUID of the quiz to generate content for
        generation_input: Input for LLM generation
        generation_port: Port for generating quiz content
    """
    # 1. Update status to GENERATING
    async with sessionmanager.session() as db:
        quiz_repo = QuizRepository(db)
        await quiz_repo.update_status(quiz_id, QuizStatus.GENERATING)
        await db.commit()

    try:
        # 2. LLM generation (no DB session - can take time)
        generated_quiz = await generation_port.generate_quiz(generation_input)

        # 3. Persist generated content
        async with sessionmanager.session() as db:
            quiz_repo = QuizRepository(db)
            task_repo = TaskRepository(db)

            # Update quiz with generated title and topic
            await quiz_repo.update_title_topic(
                quiz_id,
                generated_quiz.title,
                generated_quiz.topic,
            )

            # Create all tasks
            for idx, task in enumerate(generated_quiz.tasks):
                strategy = mapping_registry.get(task.type)
                task_model = strategy.build_model(
                    quiz_id,
                    quiz_version_id,
                    task,
                    idx,
                )
                await task_repo.save(task_model)

            # Update status to COMPLETED
            await quiz_repo.update_status(quiz_id, QuizStatus.COMPLETED)
            await db.commit()

        logger.info(f"Quiz {quiz_id} generation completed successfully")

    except Exception as e:
        # 4. Handle failure
        logger.error(f"Quiz {quiz_id} generation failed: {e}")

        async with sessionmanager.session() as db:
            quiz_repo = QuizRepository(db)
            await quiz_repo.update_status(quiz_id, QuizStatus.FAILED)
            await db.commit()

        # Re-raise to ensure error is logged by FastAPI
        raise
