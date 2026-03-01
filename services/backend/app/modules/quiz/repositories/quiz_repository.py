"""Quiz repository for database operations.

This module provides data access layer for Quiz entities.
Repository pattern: isolates database operations from business logic.
"""

import uuid
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.quiz.models.quiz import Quiz, QuizState, QuizStatus


class QuizRepository:
    """Repository for Quiz database operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            db: Async SQLAlchemy session
        """
        self.db = db

    async def create(
        self,
        title: str,
        created_by: uuid.UUID,
        topic: Optional[str] = None,
        state: QuizState = QuizState.PRIVATE,
        status: QuizStatus = QuizStatus.PENDING,
    ) -> Quiz:
        """
        Create a new quiz.

        Args:
            title: Quiz title
            created_by: UUID of the user creating the quiz
            topic: Main topic/subject of the quiz (optional)
            state: Initial visibility state (default: PRIVATE)
            status: Initial generation status (default: PENDING)

        Returns:
            Created Quiz instance
        """
        quiz = Quiz(
            title=title,
            topic=topic or "",  # Empty string if None
            created_by=created_by,
            state=state,
            status=status,
        )
        self.db.add(quiz)
        await self.db.flush()  # Flush to get the generated quiz_id
        await self.db.refresh(quiz)  # Refresh to load all fields
        return quiz

    async def get_by_id(
        self,
        quiz_id: uuid.UUID,
        load_tasks: bool = False,
    ) -> Optional[Quiz]:
        """
        Get quiz by ID.

        Args:
            quiz_id: Quiz's UUID
            load_tasks: If True, eagerly load tasks relationship

        Returns:
            Quiz instance if found, None otherwise
        """
        query = select(Quiz).where(Quiz.quiz_id == quiz_id)

        if load_tasks:
            query = query.options(selectinload(Quiz.tasks))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_user(
        self,
        user_id: uuid.UUID,
        state: Optional[QuizState] = None,
        status: Optional[QuizStatus] = None,
    ) -> List[Quiz]:
        """
        Get all quizzes created by a user with optional filters.

        Args:
            user_id: UUID of the quiz creator
            state: Optional state filter (PRIVATE/PROTECTED/PUBLIC)
            status: Optional status filter (PENDING/GENERATING/COMPLETED/FAILED)

        Returns:
            List of Quiz instances, ordered by created_at desc
        """
        query = select(Quiz).where(Quiz.created_by == user_id)

        # Apply optional filters
        if state is not None:
            query = query.where(Quiz.state == state)

        if status is not None:
            query = query.where(Quiz.status == status)

        # Order by most recent first
        query = query.order_by(Quiz.created_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def _update_quiz(self, quiz_id: uuid.UUID, **updates) -> Optional[Quiz]:
        """
        Internal helper to update quiz fields.

        Args:
            quiz_id: Quiz's UUID
            **updates: Field-value pairs to update

        Returns:
            Updated Quiz instance if found, None otherwise
        """
        quiz = await self.get_by_id(quiz_id)
        if quiz is None:
            return None
        for key, value in updates.items():
            setattr(quiz, key, value)
        await self.db.flush()
        await self.db.refresh(quiz)
        return quiz

    async def update_status(
        self,
        quiz_id: uuid.UUID,
        status: QuizStatus,
    ) -> Optional[Quiz]:
        """Update quiz generation status."""
        return await self._update_quiz(quiz_id, status=status)

    async def update_state(
        self,
        quiz_id: uuid.UUID,
        state: QuizState,
    ) -> Optional[Quiz]:
        """Update quiz visibility state."""
        return await self._update_quiz(quiz_id, state=state)

    async def update_title_topic(
        self,
        quiz_id: uuid.UUID,
        title: str,
        topic: str,
    ) -> Optional[Quiz]:
        """Update quiz title and topic (used after LLM generation)."""
        return await self._update_quiz(quiz_id, title=title, topic=topic)

    async def delete(self, quiz_id: uuid.UUID) -> bool:
        """
        Delete a quiz by ID.

        Cascades to tasks and ownerships due to cascade="all, delete-orphan".

        Args:
            quiz_id: Quiz's UUID to delete

        Returns:
            True if quiz was deleted, False if quiz was not found
        """
        quiz = await self.get_by_id(quiz_id)
        if quiz is None:
            return False

        await self.db.delete(quiz)
        await self.db.flush()
        return True
