"""Shared port definitions for quiz read access."""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Literal, Protocol, Sequence, TypeAlias
from uuid import UUID

from fastapi import Depends


class QuizAccessView(Protocol):
    """Minimal view of quiz access metadata used by other modules."""

    quiz_id: UUID
    status: str | Enum
    state: str | Enum


class MultipleChoiceOptionView(Protocol):
    """Minimal view of a multiple choice option."""

    option_id: UUID
    is_correct: bool


class ClozeBlankView(Protocol):
    """Minimal view of a cloze blank."""

    blank_id: UUID
    expected_value: str


class TaskDetailBaseView(Protocol):
    """Common task fields used by other modules."""

    task_id: UUID
    quiz_id: UUID
    type: Literal["multiple_choice", "free_text", "cloze"]


class TaskDetailMultipleChoiceView(TaskDetailBaseView, Protocol):
    """Task view for multiple choice tasks."""

    type: Literal["multiple_choice"]
    options: Sequence[MultipleChoiceOptionView]


class TaskDetailFreeTextView(TaskDetailBaseView, Protocol):
    """Task view for free text tasks."""

    type: Literal["free_text"]


class TaskDetailClozeView(TaskDetailBaseView, Protocol):
    """Task view for cloze tasks."""

    type: Literal["cloze"]
    blanks: Sequence[ClozeBlankView]


TaskDetailView: TypeAlias = (
    TaskDetailMultipleChoiceView | TaskDetailFreeTextView | TaskDetailClozeView
)


class QuizReadPort(Protocol):
    """Port for reading quiz data from other modules."""

    async def get_quiz_access(
        self,
        quiz_id: UUID,
        user_id: UUID,
    ) -> QuizAccessView:
        """Return access-checked quiz metadata."""

    async def get_tasks(
        self,
        quiz_id: UUID,
        user_id: UUID,
    ) -> Sequence[TaskDetailView]:
        """Return access-checked tasks for a quiz."""

    async def get_task(
        self,
        task_id: UUID,
        user_id: UUID,
    ) -> TaskDetailView:
        """Return access-checked task by ID."""


def get_quiz_read_port() -> QuizReadPort:
    """Shared dependency hook for quiz read access."""
    raise NotImplementedError("QuizReadPort is not configured")


QuizReadPortDep = Annotated[QuizReadPort, Depends(get_quiz_read_port)]


__all__ = [
    "ClozeBlankView",
    "MultipleChoiceOptionView",
    "QuizAccessView",
    "QuizReadPort",
    "QuizReadPortDep",
    "TaskDetailBaseView",
    "TaskDetailClozeView",
    "TaskDetailFreeTextView",
    "TaskDetailMultipleChoiceView",
    "TaskDetailView",
    "get_quiz_read_port",
]
