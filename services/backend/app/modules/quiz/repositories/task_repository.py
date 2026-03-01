"""Task repository for database operations.

This module provides data access layer for Task entities (polymorphic).
Repository pattern: isolates database operations from business logic.

Handles all task types: MultipleChoiceTask, FreeTextTask, ClozeTask.
SQLAlchemy automatically returns the correct subclass when querying Task.
"""

import uuid
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import with_polymorphic

from app.modules.quiz.models.quiz_version import QuizVersion
from app.modules.quiz.models.task import (
    Task,
    TaskType,
    MultipleChoiceTask,
    FreeTextTask,
    ClozeTask,
)


class TaskRepository:
    """Repository for Task database operations (all types)."""

    def __init__(self, db: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            db: Async SQLAlchemy session
        """
        self.db = db

    def _get_polymorphic_entity(self):
        """Get polymorphic entity for Task queries with all subtypes."""
        return with_polymorphic(Task, [MultipleChoiceTask, FreeTextTask, ClozeTask])

    async def _load_task_relationships(self, task: Task) -> None:
        """
        Load nested relationships for a task based on its type.

        Args:
            task: Task instance (may be MultipleChoiceTask or ClozeTask)
        """
        if isinstance(task, MultipleChoiceTask):
            await self.db.refresh(task, ["options"])
        elif isinstance(task, ClozeTask):
            await self.db.refresh(task, ["blanks"])

    async def get_by_ids(self, task_ids: list[uuid.UUID]) -> list[Task]:
        """
        Get multiple tasks by their IDs with eager loading.

        Args:
            task_ids: List of Task UUIDs

        Returns:
            List of Task subclass instances found
        """
        if not task_ids:
            return []
        poly_task = self._get_polymorphic_entity()
        query = select(poly_task).where(poly_task.task_id.in_(task_ids))
        result = await self.db.execute(query)
        tasks = list(result.scalars().all())
        for task in tasks:
            await self._load_task_relationships(task)
        return tasks

    async def get_by_id(self, task_id: uuid.UUID) -> Optional[Task]:
        """
        Get task by ID.

        SQLAlchemy automatically returns the correct subclass
        (MultipleChoiceTask/FreeTextTask/ClozeTask) based on polymorphic identity.

        Eagerly loads nested entities:
        - MultipleChoiceTask.options
        - ClozeTask.blanks

        Args:
            task_id: Task's UUID

        Returns:
            Task subclass instance if found, None otherwise
        """
        # Use with_polymorphic to eagerly load all subclass columns
        # This is required for async SQLAlchemy to avoid lazy loading issues
        poly_task = self._get_polymorphic_entity()
        query = select(poly_task).where(poly_task.task_id == task_id)
        result = await self.db.execute(query)
        task = result.scalar_one_or_none()

        if task is None:
            return None

        # Explicitly load nested relationships based on task type
        # This ensures compatibility with async SQLite (aiosqlite)
        await self._load_task_relationships(task)

        return task

    async def get_by_quiz_version(self, quiz_version_id: uuid.UUID) -> list[Task]:
        """
        Get all tasks for a specific quiz version, ordered by order_index.

        Args:
            quiz_version_id: UUID of the quiz version

        Returns:
            List of Task subclass instances, ordered by order_index
        """
        poly_task = self._get_polymorphic_entity()
        query = (
            select(poly_task)
            .where(poly_task.quiz_version_id == quiz_version_id)
            .order_by(poly_task.order_index)
        )

        result = await self.db.execute(query)
        tasks = list(result.scalars().all())

        for task in tasks:
            await self._load_task_relationships(task)

        return tasks

    async def save_many(self, tasks: list[Task]) -> list[Task]:
        """
        Persist multiple tasks and their nested entities.

        Args:
            tasks: List of Task instances to persist

        Returns:
            Persisted Task instances
        """
        if not tasks:
            return []
        self.db.add_all(tasks)
        await self.db.flush()
        return tasks

    async def list_types_by_quiz_ids(
        self,
        quiz_ids: list[uuid.UUID],
    ) -> list[tuple[uuid.UUID, TaskType]]:
        """
        Get task type entries for a list of quizzes.

        Args:
            quiz_ids: List of quiz UUIDs

        Returns:
            List of (quiz_id, task_type) rows
        """
        if not quiz_ids:
            return []

        result = await self.db.execute(
            select(Task.quiz_id, Task.type)
            .join(
                QuizVersion,
                QuizVersion.quiz_version_id == Task.quiz_version_id,
            )
            .where(
                Task.quiz_id.in_(quiz_ids),
                Task.quiz_version_id == QuizVersion.quiz_version_id,
                QuizVersion.is_current.is_(True),
            ),
        )
        return list(result.all())

    async def save(self, task: Task) -> Task:
        """
        Persist a task and its nested entities.

        Args:
            task: Task instance (may include options/blanks)

        Returns:
            Persisted Task instance
        """
        self.db.add(task)
        await self.db.flush()
        await self._load_task_relationships(task)
        return task

    async def delete(self, task_id: uuid.UUID) -> bool:
        """
        Delete a task by ID.

        Cascades to nested entities (options, blanks) due to cascade="all, delete-orphan".

        Args:
            task_id: Task's UUID to delete

        Returns:
            True if task was deleted, False if task was not found
        """
        task = await self.get_by_id(task_id)
        if task is None:
            return False

        await self.db.delete(task)
        await self.db.flush()
        return True

    async def get_max_order_index(self, quiz_id: uuid.UUID) -> int:
        """
        Get the maximum order_index for tasks in the current quiz version.

        Useful for determining the next order_index when adding a new task.

        Args:
            quiz_id: UUID of the quiz

        Returns:
            Maximum order_index, or -1 if no tasks exist
        """
        result = await self.db.execute(
            select(func.max(Task.order_index))
            .join(
                QuizVersion,
                QuizVersion.quiz_version_id == Task.quiz_version_id,
            )
            .where(
                QuizVersion.quiz_id == quiz_id,
                Task.quiz_version_id == QuizVersion.quiz_version_id,
                QuizVersion.is_current.is_(True),
            ),
        )
        max_index = result.scalar_one_or_none()
        return max_index if max_index is not None else -1
