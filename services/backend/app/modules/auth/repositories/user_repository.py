"""User repository for database operations.

This module provides data access layer for User entities.
Repository pattern: isolates database operations from business logic.
"""

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import User


class UserRepository:
    """Repository for User database operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            db: Async SQLAlchemy session
        """
        self.db = db

    async def create(self, email_hash: str) -> User:
        """
        Create a new user with the given email hash.

        Args:
            email_hash: SHA-256 hash of the user's email

        Returns:
            Created User instance

        Raises:
            IntegrityError: If email_hash already exists (unique constraint)
        """
        user = User(email_hash=email_hash)
        self.db.add(user)
        await self.db.flush()  # Flush to get the generated user_id
        await self.db.refresh(user)  # Refresh to load all fields
        return user

    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """
        Get user by ID.

        Args:
            user_id: User's UUID

        Returns:
            User instance if found, None otherwise
        """
        result = await self.db.execute(select(User).where(User.user_id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email_hash(self, email_hash: str) -> Optional[User]:
        """
        Get user by email hash.

        Args:
            email_hash: SHA-256 hash of the email address

        Returns:
            User instance if found, None otherwise
        """
        result = await self.db.execute(
            select(User).where(User.email_hash == email_hash),
        )
        return result.scalar_one_or_none()

    async def exists_by_email_hash(self, email_hash: str) -> bool:
        """
        Check if a user with the given email hash exists.

        Args:
            email_hash: SHA-256 hash of the email address

        Returns:
            True if user exists, False otherwise
        """
        user = await self.get_by_email_hash(email_hash)
        return user is not None

    async def delete(self, user_id: uuid.UUID) -> bool:
        """
        Delete a user by ID.

        Args:
            user_id: User's UUID to delete

        Returns:
            True if user was deleted, False if user was not found
        """
        user = await self.get_by_id(user_id)
        if user is None:
            return False

        await self.db.delete(user)
        await self.db.flush()
        return True
