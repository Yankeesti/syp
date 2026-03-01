"""Quiz edit session repository for database operations."""

from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.quiz.models.quiz_edit_session import (
    QuizEditSession,
    QuizEditSessionStatus,
)


class QuizEditSessionRepository:
    """Repository for QuizEditSession database operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        quiz_id: uuid.UUID,
        draft_version_id: uuid.UUID,
        started_by: uuid.UUID,
    ) -> QuizEditSession:
        session = QuizEditSession(
            quiz_id=quiz_id,
            draft_version_id=draft_version_id,
            started_by=started_by,
            status=QuizEditSessionStatus.ACTIVE,
        )
        self.db.add(session)
        await self.db.flush()
        await self.db.refresh(session)
        return session

    async def get_by_id(self, edit_session_id: uuid.UUID) -> Optional[QuizEditSession]:
        result = await self.db.execute(
            select(QuizEditSession).where(
                QuizEditSession.edit_session_id == edit_session_id,
            ),
        )
        return result.scalar_one_or_none()

    async def get_active_for_quiz(
        self,
        quiz_id: uuid.UUID,
    ) -> Optional[QuizEditSession]:
        result = await self.db.execute(
            select(QuizEditSession).where(
                QuizEditSession.quiz_id == quiz_id,
                QuizEditSession.status == QuizEditSessionStatus.ACTIVE,
            ),
        )
        return result.scalar_one_or_none()

    async def update_status(
        self,
        edit_session_id: uuid.UUID,
        status: QuizEditSessionStatus,
    ) -> Optional[QuizEditSession]:
        session = await self.get_by_id(edit_session_id)
        if session is None:
            return None
        session.status = status
        await self.db.flush()
        await self.db.refresh(session)
        return session

    async def delete(self, edit_session_id: uuid.UUID) -> bool:
        session = await self.get_by_id(edit_session_id)
        if session is None:
            return False
        await self.db.delete(session)
        await self.db.flush()
        return True
