"""Task clone strategies for different task types."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.modules.quiz.models.task import (
    Task,
    MultipleChoiceTask,
    TaskMultipleChoiceOption,
    FreeTextTask,
    ClozeTask,
    TaskClozeBlank,
)
from app.modules.quiz.strategies.task_mapping_strategy import TaskTypeKey


class TaskCloneStrategy(Protocol):
    """Clone strategy for a specific task type."""

    task_type: TaskTypeKey

    def clone(self, task: Task, target_version_id: UUID) -> Task:
        """Clone a task into a new quiz version."""


class MultipleChoiceTaskCloneStrategy:
    """Clone strategy for multiple choice tasks."""

    task_type: TaskTypeKey = "multiple_choice"

    def clone(self, task: Task, target_version_id: UUID) -> Task:
        if not isinstance(task, MultipleChoiceTask):
            raise ValueError(f"Expected MultipleChoiceTask, got {type(task).__name__}")

        options = [
            TaskMultipleChoiceOption(
                text=opt.text,
                is_correct=opt.is_correct,
                explanation=opt.explanation,
            )
            for opt in (task.options or [])
        ]

        return MultipleChoiceTask(
            quiz_id=task.quiz_id,
            quiz_version_id=target_version_id,
            prompt=task.prompt,
            topic_detail=task.topic_detail,
            order_index=task.order_index,
            options=options,
        )


class FreeTextTaskCloneStrategy:
    """Clone strategy for free text tasks."""

    task_type: TaskTypeKey = "free_text"

    def clone(self, task: Task, target_version_id: UUID) -> Task:
        if not isinstance(task, FreeTextTask):
            raise ValueError(f"Expected FreeTextTask, got {type(task).__name__}")

        return FreeTextTask(
            quiz_id=task.quiz_id,
            quiz_version_id=target_version_id,
            prompt=task.prompt,
            topic_detail=task.topic_detail,
            order_index=task.order_index,
            reference_answer=task.reference_answer,
        )


class ClozeTaskCloneStrategy:
    """Clone strategy for cloze tasks."""

    task_type: TaskTypeKey = "cloze"

    def clone(self, task: Task, target_version_id: UUID) -> Task:
        if not isinstance(task, ClozeTask):
            raise ValueError(f"Expected ClozeTask, got {type(task).__name__}")

        blanks = [
            TaskClozeBlank(
                position=blank.position,
                expected_value=blank.expected_value,
            )
            for blank in (task.blanks or [])
        ]

        return ClozeTask(
            quiz_id=task.quiz_id,
            quiz_version_id=target_version_id,
            prompt=task.prompt,
            topic_detail=task.topic_detail,
            order_index=task.order_index,
            template_text=task.template_text,
            blanks=blanks,
        )
