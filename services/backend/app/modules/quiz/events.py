"""Quiz module event publisher implementation."""

from __future__ import annotations

from functools import lru_cache

from app.shared.ports.quiz_events import (
    QuizDeletedEvent,
    QuizDeletedHandler,
    QuizEventPublisher,
)


class InMemoryQuizEventPublisher(QuizEventPublisher):
    """In-memory quiz event publisher for intra-process subscriptions."""

    def __init__(self) -> None:
        self._quiz_deleted_handlers: list[QuizDeletedHandler] = []

    def subscribe_quiz_deleted(self, handler: QuizDeletedHandler) -> None:
        self._quiz_deleted_handlers.append(handler)

    async def publish_quiz_deleted(self, event: QuizDeletedEvent) -> None:
        for handler in self._quiz_deleted_handlers:
            await handler(event)


@lru_cache
def get_quiz_event_publisher() -> QuizEventPublisher:
    """Singleton publisher for quiz lifecycle events."""
    return InMemoryQuizEventPublisher()


__all__ = [
    "InMemoryQuizEventPublisher",
    "get_quiz_event_publisher",
]
