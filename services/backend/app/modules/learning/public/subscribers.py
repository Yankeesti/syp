"""Learning module subscribers for quiz events."""

from __future__ import annotations

from app.modules.learning.repositories import AttemptRepository
from app.modules.learning.services.cleanup_service import LearningCleanupService
from app.shared.ports.quiz_events import QuizDeletedEvent, QuizEventPublisher


async def handle_quiz_deleted(event: QuizDeletedEvent) -> None:
    """Handle quiz deletion by removing related attempts."""
    service = LearningCleanupService(AttemptRepository(event.db))
    await service.delete_attempts_for_quiz(event.quiz_id)


def register_quiz_subscribers(publisher: QuizEventPublisher) -> None:
    """Register learning subscribers for quiz events."""
    publisher.subscribe_quiz_deleted(handle_quiz_deleted)


__all__ = ["register_quiz_subscribers"]
