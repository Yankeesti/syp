"""Quiz version repository for database operations."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.quiz.models.quiz_version import QuizVersion, QuizVersionStatus


class QuizVersionRepository:
    """Repository for QuizVersion database operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_draft(
        self,
        quiz_id: uuid.UUID,
        created_by: uuid.UUID,
        base_version_id: uuid.UUID | None = None,
    ) -> QuizVersion:
        version = QuizVersion(
            quiz_id=quiz_id,
            created_by=created_by,
            base_version_id=base_version_id,
            status=QuizVersionStatus.DRAFT,
        )
        self.db.add(version)
        await self.db.flush()
        await self.db.refresh(version)
        return version

    async def create_published(
        self,
        quiz_id: uuid.UUID,
        created_by: uuid.UUID,
        version_number: int,
        committed_at: datetime | None = None,
        is_current: bool = False,
    ) -> QuizVersion:
        version = QuizVersion(
            quiz_id=quiz_id,
            created_by=created_by,
            status=QuizVersionStatus.PUBLISHED,
            version_number=version_number,
            committed_at=committed_at or datetime.now(timezone.utc),
            is_current=is_current,
        )
        self.db.add(version)
        await self.db.flush()
        await self.db.refresh(version)
        return version

    async def get_by_id(self, quiz_version_id: uuid.UUID) -> Optional[QuizVersion]:
        result = await self.db.execute(
            select(QuizVersion).where(QuizVersion.quiz_version_id == quiz_version_id),
        )
        return result.scalar_one_or_none()

    async def get_current_version_id(self, quiz_id: uuid.UUID) -> uuid.UUID | None:
        result = await self.db.execute(
            select(QuizVersion.quiz_version_id).where(
                QuizVersion.quiz_id == quiz_id,
                QuizVersion.is_current.is_(True),
            ),
        )
        return result.scalar_one_or_none()

    async def get_latest_version_number(self, quiz_id: uuid.UUID) -> int | None:
        result = await self.db.execute(
            select(func.max(QuizVersion.version_number)).where(
                QuizVersion.quiz_id == quiz_id,
            ),
        )
        return result.scalar_one_or_none()

    async def set_current_version(
        self,
        quiz_id: uuid.UUID,
        quiz_version_id: uuid.UUID,
    ) -> None:
        await self.db.execute(
            update(QuizVersion)
            .where(
                QuizVersion.quiz_id == quiz_id,
                QuizVersion.is_current.is_(True),
            )
            .values(is_current=False),
        )
        await self.db.execute(
            update(QuizVersion)
            .where(
                QuizVersion.quiz_version_id == quiz_version_id,
                QuizVersion.quiz_id == quiz_id,
            )
            .values(is_current=True),
        )

    async def publish_version(
        self,
        quiz_version_id: uuid.UUID,
        version_number: int,
    ) -> Optional[QuizVersion]:
        version = await self.get_by_id(quiz_version_id)
        if version is None:
            return None
        version.status = QuizVersionStatus.PUBLISHED
        version.version_number = version_number
        version.committed_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(version)
        return version

    async def delete(self, quiz_version_id: uuid.UUID) -> bool:
        version = await self.get_by_id(quiz_version_id)
        if version is None:
            return False
        await self.db.delete(version)
        await self.db.flush()
        return True
