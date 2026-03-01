"""Task service for business logic.

This module provides business logic orchestration for Task entities.
Service layer: coordinates repositories, handles authorization.

Task Generation Flow (handled by background worker):
-----------------------------------------------------
1. QuizRouter creates Quiz with status="pending"
2. Background worker picks up the quiz and:
   a) Updates status to "generating"
   b) Calls QuizGenerationPort.generate_quiz(...)
   c) LLM returns all tasks as structured JSON in one response
   d) Tasks are persisted via TaskRepository
   e) Status is updated to "completed" (or "failed" on error)
3. Frontend polls GET /quizzes/{quiz_id} until status != "pending"/"generating"

Note: Tasks are generated and persisted in bulk, not individually.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.quiz.repositories.task_repository import TaskRepository
from app.modules.quiz.repositories.quiz_ownership_repository import (
    QuizOwnershipRepository,
)
from app.modules.quiz.models import (
    Task,
    OwnershipRole,
)
from app.modules.quiz.exceptions import (
    TaskNotFoundException,
    AccessDeniedException,
    TaskTypeMismatchException,
    EditSessionRequiredException,
    EditSessionTaskMismatchException,
)
from app.modules.quiz.schemas import TaskUpdateDto, TaskDetailDto
from app.modules.quiz.strategies import (
    TaskMappingRegistry,
    TaskUpdateRegistry,
    normalize_task_type,
)
from app.modules.quiz.services.edit_session_service import QuizEditSessionService


class TaskService:
    """Service for Task business logic."""

    def __init__(
        self,
        db: AsyncSession,
        task_repo: TaskRepository,
        ownership_repo: QuizOwnershipRepository,
        edit_session_service: QuizEditSessionService,
        mapping_registry: TaskMappingRegistry,
        update_registry: TaskUpdateRegistry,
    ) -> None:
        """
        Initialize service with database session and repositories.

        Args:
            db: Async SQLAlchemy session
            task_repo: Task repository instance
            ownership_repo: Quiz ownership repository instance
            edit_session_service: Edit session service instance
        """
        self.db = db
        self.task_repo = task_repo
        self.ownership_repo = ownership_repo
        self.edit_session_service = edit_session_service
        self.task_mapping_registry = mapping_registry
        self.task_update_registry = update_registry

    async def get_tasks_batch(
        self,
        task_ids: list[uuid.UUID],
        user_id: uuid.UUID,
    ) -> list[TaskDetailDto]:
        """
        Load multiple tasks by ID with access check.

        Args:
            task_ids: List of task UUIDs to load
            user_id: UUID of the requesting user

        Returns:
            List of task detail DTOs

        Raises:
            AccessDeniedException: If user lacks access to any referenced quiz
        """
        tasks = await self.task_repo.get_by_ids(task_ids)

        # Collect unique quiz_ids and check access
        quiz_ids = {t.quiz_id for t in tasks}
        for quiz_id in quiz_ids:
            has_access = await self.ownership_repo.user_has_access(
                quiz_id=quiz_id,
                user_id=user_id,
            )
            if not has_access:
                raise AccessDeniedException("No access to quiz")

        return [
            self.task_mapping_registry.get(normalize_task_type(t.type)).to_dto(t)
            for t in tasks
        ]

    async def delete_task(
        self,
        task_id: uuid.UUID,
        user_id: uuid.UUID,
        edit_session_id: uuid.UUID | None,
    ) -> None:
        """
        Delete a task.

        Only users with EDITOR or OWNER role can delete tasks.
        Cascades to nested entities (options, blanks).

        Args:
            task_id: UUID of the task to delete
            user_id: UUID of the user requesting deletion
            edit_session_id: UUID of the active edit session

        Raises:
            TaskNotFoundException: If task not found
            AccessDeniedException: If user lacks permission
        """
        task = await self._require_editable_task(
            task_id,
            user_id,
            edit_session_id,
            "You do not have permission to delete this task",
        )

        await self.task_repo.delete(task_id)
        await self.db.commit()

    async def update_task(
        self,
        task_id: uuid.UUID,
        user_id: uuid.UUID,
        update_dto: TaskUpdateDto,
        edit_session_id: uuid.UUID | None,
    ) -> TaskDetailDto:
        """
        Update a task.

        Only users with EDITOR or OWNER role can update tasks.
        The update DTO type must match the task's actual type.

        Args:
            task_id: UUID of the task to update
            user_id: UUID of the user requesting the update
            update_dto: Update data (discriminated union by task type)
            edit_session_id: UUID of the active edit session

        Returns:
            Updated task as response DTO

        Raises:
            TaskNotFoundException: If task not found
            AccessDeniedException: If user lacks permission
            TaskTypeMismatchException: If DTO type doesn't match task type
        """
        # 1. Load task and validate session/permissions
        task = await self._require_editable_task(
            task_id,
            user_id,
            edit_session_id,
            "You do not have permission to update this task",
        )

        # 3. Validate task type matches DTO type
        task_type = normalize_task_type(task.type)
        dto_type = update_dto.type

        if task_type != dto_type:
            raise TaskTypeMismatchException(
                expected_type=task_type,
                actual_type=dto_type,
            )

        # 4. Apply update via strategy
        update_strategy = self.task_update_registry.get(task_type)
        updated_task = update_strategy.apply_update(task, update_dto)

        # 5. Persist changes
        await self.db.commit()
        await self.task_repo._load_task_relationships(updated_task)

        # 6. Map to response DTO
        mapping_strategy = self.task_mapping_registry.get(task_type)
        return mapping_strategy.to_dto(updated_task)

    async def _require_editable_task(
        self,
        task_id: uuid.UUID,
        user_id: uuid.UUID,
        edit_session_id: uuid.UUID | None,
        access_denied_message: str,
    ) -> Task:
        if edit_session_id is None:
            raise EditSessionRequiredException()

        session = await self.edit_session_service.require_active_session(
            edit_session_id,
            user_id,
        )

        task = await self.task_repo.get_by_id(task_id)
        if task is None:
            raise TaskNotFoundException()

        if task.quiz_version_id != session.draft_version_id:
            raise EditSessionTaskMismatchException()

        has_access = await self.ownership_repo.user_has_access(
            quiz_id=task.quiz_id,
            user_id=user_id,
            required_role=OwnershipRole.EDITOR,
        )
        if not has_access:
            raise AccessDeniedException(access_denied_message)

        return task
