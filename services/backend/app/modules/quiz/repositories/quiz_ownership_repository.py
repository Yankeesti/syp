"""Quiz ownership repository for database operations.

This module provides data access layer for QuizOwnership entities.
Repository pattern: isolates database operations from business logic.
"""

import uuid
from typing import Optional, List

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.quiz.models.quiz_ownership import QuizOwnership, OwnershipRole
from app.modules.quiz.models.quiz import Quiz


class QuizOwnershipRepository:
    """Repository for QuizOwnership database operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            db: Async SQLAlchemy session
        """
        self.db = db

    async def create(
        self,
        quiz_id: uuid.UUID,
        user_id: uuid.UUID,
        role: OwnershipRole = OwnershipRole.OWNER,
    ) -> QuizOwnership:
        """
        Create a new quiz ownership record.

        Args:
            quiz_id: UUID of the quiz
            user_id: UUID of the user
            role: Ownership role (default: OWNER)

        Returns:
            Created QuizOwnership instance

        Raises:
            IntegrityError: If quiz_id + user_id combination already exists
        """
        ownership = QuizOwnership(
            quiz_id=quiz_id,
            user_id=user_id,
            role=role,
        )
        self.db.add(ownership)
        await self.db.flush()  # Flush to detect constraint violations
        await self.db.refresh(ownership)  # Refresh to load all fields
        return ownership

    async def get_by_quiz_and_user(
        self,
        quiz_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Optional[QuizOwnership]:
        """
        Get ownership record for a specific quiz and user.

        Args:
            quiz_id: UUID of the quiz
            user_id: UUID of the user

        Returns:
            QuizOwnership instance if found, None otherwise
        """
        result = await self.db.execute(
            select(QuizOwnership).where(
                QuizOwnership.quiz_id == quiz_id,
                QuizOwnership.user_id == user_id,
            ),
        )
        return result.scalar_one_or_none()

    async def user_has_access(
        self,
        quiz_id: uuid.UUID,
        user_id: uuid.UUID,
        required_role: Optional[OwnershipRole] = None,
    ) -> bool:
        """
        Check if user has access to a quiz with optional role hierarchy check.

        Role hierarchy: OWNER > EDITOR > VIEWER

        Args:
            quiz_id: UUID of the quiz
            user_id: UUID of the user
            required_role: Minimum required role (None = any role is sufficient)

        Returns:
            True if user has sufficient access, False otherwise
        """
        ownership = await self.get_by_quiz_and_user(quiz_id, user_id)

        if ownership is None:
            return False

        # If no specific role is required, any ownership grants access
        if required_role is None:
            return True

        return ownership.role.has_permission_for(required_role)

    async def delete_by_quiz(self, quiz_id: uuid.UUID) -> int:
        """
        Delete all ownership records for a quiz.

        Used when a quiz is deleted (cascade) or when removing all shares.

        Args:
            quiz_id: UUID of the quiz

        Returns:
            Number of ownership records deleted
        """
        result = await self.db.execute(
            delete(QuizOwnership).where(QuizOwnership.quiz_id == quiz_id),
        )
        await self.db.flush()
        return result.rowcount

    async def get_quizzes_by_user(
        self,
        user_id: uuid.UUID,
        roles: Optional[List[OwnershipRole]] = None,
    ) -> List[tuple[Quiz, OwnershipRole]]:
        """
        Get all quizzes where user has ownership, with optional role filtering.

        Args:
            user_id: UUID of the user
            roles: Optional list of roles to filter by (None = all roles)

        Returns:
            List of tuples (Quiz, OwnershipRole), ordered by created_at desc
        """
        query = (
            select(Quiz, QuizOwnership.role)
            .join(QuizOwnership, Quiz.quiz_id == QuizOwnership.quiz_id)
            .where(QuizOwnership.user_id == user_id)
        )

        if roles:
            query = query.where(QuizOwnership.role.in_(roles))

        query = query.order_by(Quiz.created_at.desc())

        result = await self.db.execute(query)
        return list(result.all())
