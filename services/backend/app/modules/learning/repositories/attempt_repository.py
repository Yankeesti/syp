"""Attempt repository for database operations.

This module provides data access layer for Attempt entities.
Repository pattern: isolates database operations from business logic.

Handles attempt lifecycle:
- Creating new attempts
- Querying open/existing attempts
- Marking attempts as evaluated
- Cleanup operations
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.learning.models import Attempt, AttemptStatus


class AttemptRepository:
    """Repository for Attempt database operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            db: Async SQLAlchemy session
        """
        self.db = db

    async def create_attempt(self, user_id: UUID, quiz_id: UUID) -> Attempt:
        """
        Create a new attempt for a user and quiz.

        Args:
            user_id: UUID of the user
            quiz_id: UUID of the quiz

        Returns:
            Created Attempt instance with status IN_PROGRESS
        """
        attempt = Attempt(
            user_id=user_id,
            quiz_id=quiz_id,
            status=AttemptStatus.IN_PROGRESS,
        )
        self.db.add(attempt)
        await self.db.flush()
        return attempt

    async def get_open_attempt(self, user_id: UUID, quiz_id: UUID) -> Attempt | None:
        """
        Get an open (in_progress) attempt for user and quiz, if exists.

        Used to check if user has an ongoing attempt before creating a new one.

        Args:
            user_id: UUID of the user
            quiz_id: UUID of the quiz

        Returns:
            Attempt instance if found, None otherwise
        """
        stmt = select(Attempt).where(
            Attempt.user_id == user_id,
            Attempt.quiz_id == quiz_id,
            Attempt.status == AttemptStatus.IN_PROGRESS,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, attempt_id: UUID) -> Attempt | None:
        """
        Get attempt by ID.

        Args:
            attempt_id: UUID of the attempt

        Returns:
            Attempt instance if found, None otherwise
        """
        return await self.db.get(Attempt, attempt_id)

    async def get_by_id_with_answers(self, attempt_id: UUID) -> Attempt | None:
        """
        Get attempt by ID with all answers eagerly loaded.

        Used when evaluation needs access to all answers.

        Args:
            attempt_id: UUID of the attempt

        Returns:
            Attempt instance with answers loaded if found, None otherwise
        """
        stmt = (
            select(Attempt)
            .where(Attempt.attempt_id == attempt_id)
            .options(selectinload(Attempt.answers))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_evaluated(
        self,
        attempt_id: UUID,
        total_percentage: Decimal,
        evaluated_at: datetime,
    ) -> None:
        """
        Mark attempt as evaluated with result.

        Updates attempt status to EVALUATED and sets evaluation data.

        Args:
            attempt_id: UUID of the attempt
            total_percentage: Overall score as percentage (0-100)
            evaluated_at: Timestamp when evaluation was completed
        """
        stmt = select(Attempt).where(Attempt.attempt_id == attempt_id)
        result = await self.db.execute(stmt)
        attempt = result.scalar_one_or_none()
        if attempt:
            attempt.status = AttemptStatus.EVALUATED
            attempt.total_percentage = total_percentage
            attempt.evaluated_at = evaluated_at
            await self.db.flush()

    async def list_by_user(
        self,
        user_id: UUID,
        quiz_id: UUID | None = None,
        status: AttemptStatus | None = None,
    ) -> list[Attempt]:
        """
        Get all attempts for a user with optional filters.

        Args:
            user_id: UUID of the user
            quiz_id: Optional UUID to filter by quiz
            status: Optional status to filter by

        Returns:
            List of Attempt instances ordered by started_at descending
        """
        stmt = select(Attempt).where(Attempt.user_id == user_id)

        if quiz_id is not None:
            stmt = stmt.where(Attempt.quiz_id == quiz_id)

        if status is not None:
            stmt = stmt.where(Attempt.status == status)

        stmt = stmt.order_by(Attempt.started_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def delete_by_quiz_id(self, quiz_id: UUID) -> int:
        """
        Delete all attempts for a quiz (cleanup).

        Used when a quiz is deleted to clean up related attempts.
        Cascades to answers due to cascade="all, delete-orphan".

        Args:
            quiz_id: UUID of the quiz

        Returns:
            Count of deleted attempts
        """
        result = await self.db.execute(
            delete(Attempt).where(Attempt.quiz_id == quiz_id),
        )
        # result.rowcount can be None depending on backend; coerce to int
        deleted = result.rowcount if result.rowcount is not None else 0
        await self.db.flush()
        return int(deleted)
