"""Magic Link Token repository for database operations.

This module provides data access layer for MagicLinkToken entities.
Repository pattern: isolates database operations from business logic.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import MagicLinkToken


class MagicLinkTokenRepository:
    """Repository for MagicLinkToken database operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            db: Async SQLAlchemy session
        """
        self.db = db

    async def create(
        self,
        token_hash: str,
        email_hash: str,
        expires_at: datetime,
    ) -> MagicLinkToken:
        """
        Create a new magic link token.

        Args:
            token_hash: SHA-256 hash of the token
            email_hash: SHA-256 hash of the user's email
            expires_at: Expiration timestamp

        Returns:
            Created MagicLinkToken instance

        Raises:
            IntegrityError: If token_hash already exists (unique constraint)
        """
        magic_link_token = MagicLinkToken(
            token_hash=token_hash,
            email_hash=email_hash,
            expires_at=expires_at,
        )
        self.db.add(magic_link_token)
        await self.db.flush()  # Flush to detect constraint violations
        await self.db.refresh(magic_link_token)  # Refresh to load all fields
        return magic_link_token

    async def get_by_token_hash(self, token_hash: str) -> Optional[MagicLinkToken]:
        """
        Get magic link token by token hash.

        This is used during verification to find the token record.

        Args:
            token_hash: SHA-256 hash of the token

        Returns:
            MagicLinkToken instance if found, None otherwise
        """
        result = await self.db.execute(
            select(MagicLinkToken).where(MagicLinkToken.token_hash == token_hash),
        )
        return result.scalar_one_or_none()

    async def delete(self, token_id: uuid.UUID) -> bool:
        """
        Delete a magic link token by ID.

        Used to implement single-use tokens: after verification,
        the token is deleted to prevent reuse.

        Args:
            token_id: Token's UUID to delete

        Returns:
            True if token was deleted, False if token was not found
        """
        # Use the token object to delete
        result = await self.db.execute(
            select(MagicLinkToken).where(MagicLinkToken.id == token_id),
        )
        token = result.scalar_one_or_none()

        if token is None:
            return False

        await self.db.delete(token)
        await self.db.flush()
        return True

    async def delete_by_email_hash(self, email_hash: str) -> bool:
        """
        Delete magic link token by email hash.

        Args:
            email_hash: SHA-256 hash of the user's email

        Returns:
            True if token was deleted, False if no token existed
        """
        result = await self.db.execute(
            select(MagicLinkToken).where(MagicLinkToken.email_hash == email_hash),
        )
        token = result.scalar_one_or_none()

        if token is None:
            return False

        await self.db.delete(token)
        await self.db.flush()
        return True
