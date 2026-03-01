"""Shared port definitions for quiz event publishing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Awaitable, Callable, Protocol
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(frozen=True)
class QuizDeletedEvent:
    """Event emitted when a quiz is deleted."""

    quiz_id: UUID
    db: AsyncSession


QuizDeletedHandler = Callable[[QuizDeletedEvent], Awaitable[None]]


class QuizEventPublisher(Protocol):
    """Port for subscribing and publishing quiz lifecycle events."""

    def subscribe_quiz_deleted(self, handler: QuizDeletedHandler) -> None:
        """Register a handler for quiz deletion events."""

    async def publish_quiz_deleted(self, event: QuizDeletedEvent) -> None:
        """Publish a quiz deletion event to subscribers."""


def get_quiz_event_publisher() -> QuizEventPublisher:
    """Shared dependency hook for quiz event publishing."""
    raise NotImplementedError("QuizEventPublisher is not configured")


QuizEventPublisherDep = Annotated[
    QuizEventPublisher,
    Depends(get_quiz_event_publisher),
]


__all__ = [
    "QuizDeletedEvent",
    "QuizDeletedHandler",
    "QuizEventPublisher",
    "QuizEventPublisherDep",
    "get_quiz_event_publisher",
]
