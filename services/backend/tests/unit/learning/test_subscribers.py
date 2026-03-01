"""Tests for learning module subscribers."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.learning.public.subscribers import (
    handle_quiz_deleted,
    register_quiz_subscribers,
)
from app.shared.ports.quiz_events import QuizDeletedEvent


async def test_handle_quiz_deleted_calls_cleanup():
    """Ensure quiz deletion triggers learning cleanup."""
    quiz_id = uuid.uuid4()
    db = AsyncMock(spec=AsyncSession)
    event = QuizDeletedEvent(quiz_id=quiz_id, db=db)

    mock_repo = MagicMock()
    mock_service = MagicMock()
    mock_service.delete_attempts_for_quiz = AsyncMock()

    with (
        patch(
            "app.modules.learning.public.subscribers.AttemptRepository",
            return_value=mock_repo,
        ) as repo_cls,
        patch(
            "app.modules.learning.public.subscribers.LearningCleanupService",
            return_value=mock_service,
        ) as service_cls,
    ):
        await handle_quiz_deleted(event)

    repo_cls.assert_called_once_with(db)
    service_cls.assert_called_once_with(mock_repo)
    mock_service.delete_attempts_for_quiz.assert_awaited_once_with(quiz_id)


def test_register_quiz_subscribers_registers_handler():
    """Ensure quiz deletion handler is registered."""
    publisher = MagicMock()

    register_quiz_subscribers(publisher)

    publisher.subscribe_quiz_deleted.assert_called_once_with(handle_quiz_deleted)
