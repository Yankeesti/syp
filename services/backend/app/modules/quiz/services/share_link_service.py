"""Share link service for business logic.

This module provides business logic for share link management.
Service layer: orchestrates repositories, implements business rules, handles authorization.
"""

import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.modules.quiz.models.quiz_ownership import OwnershipRole
from app.modules.quiz.repositories.quiz_ownership_repository import (
    QuizOwnershipRepository,
)
from app.modules.quiz.repositories.quiz_repository import QuizRepository
from app.modules.quiz.repositories.share_link_repository import ShareLinkRepository
from app.modules.quiz.schemas.share_link import ShareLinkDto, ShareLinkInfoDto


class ShareLinkService:
    """Service for share link business logic and orchestration."""

    def __init__(
        self,
        db: AsyncSession,
        share_link_repo: ShareLinkRepository,
        quiz_repo: QuizRepository,
        ownership_repo: QuizOwnershipRepository,
    ):
        """
        Initialize service with database session and repositories.

        Args:
            db: Async SQLAlchemy session
            share_link_repo: Share link repository instance
            quiz_repo: Quiz repository instance
            ownership_repo: Quiz ownership repository instance
        """
        self.db = db
        self.repo = share_link_repo
        self.quiz_repo = quiz_repo
        self.ownership_repo = ownership_repo

    async def create_share_link(
        self,
        quiz_id: UUID,
        user_id: UUID,
        duration: timedelta | None = None,
        max_uses: int | None = None,
    ) -> ShareLinkDto:
        """
        Create a new share link for a quiz.

        Requires OWNER or EDITOR role on the quiz.
        Generates a cryptographically secure token and builds full URL.

        Args:
            quiz_id: UUID of the quiz to share
            user_id: UUID of the user creating the share link
            duration: Optional duration for link validity (None = never expires)
            max_uses: Optional maximum number of uses (None = unlimited)

        Returns:
            ShareLinkDto with full URL

        Raises:
            HTTPException: 403 if user lacks EDITOR permission
        """
        # Check authorization: user must have at least EDITOR role
        has_access = await self.ownership_repo.user_has_access(
            quiz_id,
            user_id,
            OwnershipRole.EDITOR,
        )
        if not has_access:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to create share links for this quiz",
            )

        # Generate secure token
        token = secrets.token_urlsafe(32)

        # Calculate expires_at from duration
        expires_at = None
        if duration is not None:
            expires_at = datetime.now(timezone.utc) + duration

        # Create share link in database
        share_link = await self.repo.create(
            quiz_id=quiz_id,
            token=token,
            created_by=user_id,
            expires_at=expires_at,
            max_uses=max_uses,
        )
        await self.db.commit()

        # Build full URL for sharing
        url = f"{get_settings().frontend_base_url}/share/{token}"

        # Return DTO with all fields
        return ShareLinkDto(
            share_link_id=share_link.share_link_id,
            quiz_id=share_link.quiz_id,
            token=share_link.token,
            url=url,
            created_at=share_link.created_at,
            expires_at=share_link.expires_at,
            max_uses=share_link.max_uses,
            current_uses=share_link.current_uses,
            is_active=share_link.is_active,
        )

    async def get_share_links(
        self,
        quiz_id: UUID,
        user_id: UUID,
    ) -> list[ShareLinkDto]:
        """
        Get all share links for a quiz.

        Requires OWNER or EDITOR role on the quiz.

        Args:
            quiz_id: UUID of the quiz
            user_id: UUID of the requesting user

        Returns:
            List of ShareLinkDto with full URLs

        Raises:
            HTTPException: 403 if user lacks EDITOR permission
        """
        # Check authorization: user must have at least EDITOR role
        has_access = await self.ownership_repo.user_has_access(
            quiz_id,
            user_id,
            OwnershipRole.EDITOR,
        )
        if not has_access:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to view share links for this quiz",
            )

        # Get all share links for the quiz
        share_links = await self.repo.get_by_quiz_id(quiz_id)

        # Build URLs and convert to DTOs
        result = []
        for link in share_links:
            url = f"{get_settings().frontend_base_url}/share/{link.token}"
            result.append(
                ShareLinkDto(
                    share_link_id=link.share_link_id,
                    quiz_id=link.quiz_id,
                    token=link.token,
                    url=url,
                    created_at=link.created_at,
                    expires_at=link.expires_at,
                    max_uses=link.max_uses,
                    current_uses=link.current_uses,
                    is_active=link.is_active,
                ),
            )

        return result

    async def revoke_share_link(
        self,
        share_link_id: UUID,
        user_id: UUID,
    ) -> None:
        """
        Revoke a share link.

        Requires OWNER or EDITOR role on the associated quiz.

        Args:
            share_link_id: UUID of the share link to revoke
            user_id: UUID of the requesting user

        Raises:
            HTTPException: 404 if share link not found
            HTTPException: 403 if user lacks EDITOR permission
        """
        # Get the share link
        share_link = await self.repo.get_by_id(share_link_id)
        if share_link is None:
            raise HTTPException(
                status_code=404,
                detail="Share link not found",
            )

        # Check authorization: user must have at least EDITOR role on the quiz
        has_access = await self.ownership_repo.user_has_access(
            share_link.quiz_id,
            user_id,
            OwnershipRole.EDITOR,
        )
        if not has_access:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to revoke this share link",
            )

        # Revoke the share link
        await self.repo.revoke(share_link_id)
        await self.db.commit()

    async def validate_share_link(self, token: str) -> ShareLinkInfoDto:
        """
        Validate a share link and return quiz information.

        Public endpoint that checks if a share link is valid and usable.
        Does not increment usage counter (call redeem for that).

        Args:
            token: Share link token to validate

        Returns:
            ShareLinkInfoDto with validation result and quiz info
        """
        # Get share link by token
        share_link = await self.repo.get_by_token(token)

        # Check if link exists
        if share_link is None:
            return ShareLinkInfoDto(
                quiz_id=None,
                quiz_title="",
                quiz_topic="",
                is_valid=False,
                error_message="Share link not found or has been revoked",
            )

        # Check if expired
        now = datetime.now(timezone.utc)
        if share_link.expires_at is not None and share_link.expires_at < now:
            return ShareLinkInfoDto(
                quiz_id=None,
                quiz_title="",
                quiz_topic="",
                is_valid=False,
                error_message="Share link has expired",
            )

        # Check if max uses reached
        if (
            share_link.max_uses is not None
            and share_link.current_uses >= share_link.max_uses
        ):
            return ShareLinkInfoDto(
                quiz_id=None,
                quiz_title="",
                quiz_topic="",
                is_valid=False,
                error_message="Share link has reached maximum uses",
            )

        # Get quiz information
        quiz = await self.quiz_repo.get_by_id(share_link.quiz_id)

        # Return valid result with quiz info
        return ShareLinkInfoDto(
            quiz_id=quiz.quiz_id,
            quiz_title=quiz.title,
            quiz_topic=quiz.topic,
            is_valid=True,
            error_message=None,
        )

    async def redeem_share_link(self, token: str, user_id: UUID) -> None:
        """
        Redeem a share link to grant quiz access.

        Creates VIEWER ownership for the user and increments usage counter.
        Uses transaction with row-level locking to prevent race conditions.

        Args:
            token: Share link token to redeem
            user_id: UUID of the user redeeming the link

        Raises:
            HTTPException: 410 if link not found, expired, or max uses reached
            HTTPException: 400 if user already has access to the quiz
        """
        # Start transaction with explicit begin
        async with self.db.begin():
            # Get share link with row-level lock
            share_link = await self.repo.get_by_token_for_update(token)

            # Check if link exists
            if share_link is None:
                raise HTTPException(
                    status_code=410,
                    detail="Share link not found or has been revoked",
                )

            # Check if expired
            now = datetime.now(timezone.utc)
            if share_link.expires_at is not None and share_link.expires_at < now:
                raise HTTPException(
                    status_code=410,
                    detail="Share link has expired",
                )

            # Check if max uses reached
            if (
                share_link.max_uses is not None
                and share_link.current_uses >= share_link.max_uses
            ):
                raise HTTPException(
                    status_code=410,
                    detail="Share link has reached maximum uses",
                )

            # Check if user already has access
            existing_ownership = await self.ownership_repo.get_by_quiz_and_user(
                share_link.quiz_id,
                user_id,
            )
            if existing_ownership is not None:
                raise HTTPException(
                    status_code=400,
                    detail="You already have access to this quiz",
                )

            # Create ownership with VIEWER role
            await self.ownership_repo.create(
                quiz_id=share_link.quiz_id,
                user_id=user_id,
                role=OwnershipRole.VIEWER,
            )

            # Increment usage counter
            await self.repo.increment_uses(share_link.share_link_id)

        # Commit the transaction
        await self.db.commit()
