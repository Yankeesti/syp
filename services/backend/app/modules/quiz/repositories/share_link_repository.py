"""Share link repository for database operations.

This module provides data access layer for ShareLink entities.
Repository pattern: isolates database operations from business logic.
"""

import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.quiz.models.share_link import ShareLink


class ShareLinkRepository:
    """Repository for ShareLink database operations."""

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
        token: str,
        created_by: uuid.UUID,
        expires_at: Optional[datetime] = None,
        max_uses: Optional[int] = None,
    ) -> ShareLink:
        """
        Create a new share link.

        Args:
            quiz_id: UUID of the quiz being shared
            token: Unique cryptographic token for the share link
            created_by: UUID of the user creating the share link
            expires_at: Optional expiration timestamp (None = never expires)
            max_uses: Optional maximum number of uses (None = unlimited)

        Returns:
            Created ShareLink instance
        """
        share_link = ShareLink(
            quiz_id=quiz_id,
            token=token,
            created_by=created_by,
            expires_at=expires_at,
            max_uses=max_uses,
        )
        self.db.add(share_link)
        await self.db.flush()  # Flush to get the generated share_link_id
        await self.db.refresh(share_link)  # Refresh to load all fields
        return share_link

    async def get_by_token(self, token: str) -> Optional[ShareLink]:
        """
        Get active share link by token.

        Args:
            token: Unique token to look up

        Returns:
            ShareLink instance if found and active, None otherwise
        """
        query = select(ShareLink).where(
            ShareLink.token == token,
            ShareLink.is_active == True,  # noqa: E712
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_id(self, share_link_id: uuid.UUID) -> Optional[ShareLink]:
        """
        Get share link by ID.

        Args:
            share_link_id: ShareLink's UUID

        Returns:
            ShareLink instance if found, None otherwise
        """
        query = select(ShareLink).where(ShareLink.share_link_id == share_link_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_quiz_id(self, quiz_id: uuid.UUID) -> List[ShareLink]:
        """
        Get all share links for a quiz.

        Args:
            quiz_id: UUID of the quiz

        Returns:
            List of ShareLink instances, ordered by created_at desc
        """
        query = (
            select(ShareLink)
            .where(ShareLink.quiz_id == quiz_id)
            .order_by(ShareLink.created_at.desc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def revoke(self, share_link_id: uuid.UUID) -> None:
        """
        Revoke a share link by setting is_active to false.

        Args:
            share_link_id: UUID of the share link to revoke
        """
        stmt = (
            update(ShareLink)
            .where(ShareLink.share_link_id == share_link_id)
            .values(is_active=False)
        )
        await self.db.execute(stmt)
        await self.db.flush()

    async def increment_uses(self, share_link_id: uuid.UUID) -> None:
        """
        Increment the current_uses counter by 1.

        Args:
            share_link_id: UUID of the share link to increment
        """
        stmt = (
            update(ShareLink)
            .where(ShareLink.share_link_id == share_link_id)
            .values(current_uses=ShareLink.current_uses + 1)
        )
        await self.db.execute(stmt)
        await self.db.flush()

    async def get_by_token_for_update(self, token: str) -> Optional[ShareLink]:
        """
        Get active share link by token with row-level lock for transaction safety.

        Use this method when you need to modify the share link (e.g., increment uses)
        to prevent race conditions.

        Args:
            token: Unique token to look up

        Returns:
            ShareLink instance if found and active, None otherwise
        """
        query = (
            select(ShareLink)
            .where(
                ShareLink.token == token,
                ShareLink.is_active == True,  # noqa: E712
            )
            .with_for_update()
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
