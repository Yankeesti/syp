"""Task update strategies for different task types.

Uses Replace-All semantics for collections (options, blanks):
- When options/blanks are provided, existing ones are removed and replaced
- When options/blanks are None, existing ones are kept unchanged
"""

from __future__ import annotations

from typing import Protocol

from app.modules.quiz.models.task import (
    Task,
    MultipleChoiceTask,
    TaskMultipleChoiceOption,
    FreeTextTask,
    ClozeTask,
    TaskClozeBlank,
)
from app.modules.quiz.schemas.task_input import (
    TaskUpdateDto,
    MultipleChoiceTaskUpdate,
    FreeTextTaskUpdate,
    ClozeTaskUpdate,
)
from app.modules.quiz.strategies.task_mapping_strategy import TaskTypeKey


class TaskUpdateStrategy(Protocol):
    """Update strategy for a specific task type."""

    task_type: TaskTypeKey

    def apply_update(self, task: Task, update_dto: TaskUpdateDto) -> Task:
        """Apply update to existing task and return the updated model."""


class MultipleChoiceTaskUpdateStrategy:
    """Update strategy for multiple choice tasks."""

    task_type: TaskTypeKey = "multiple_choice"

    def apply_update(self, task: Task, update_dto: TaskUpdateDto) -> Task:
        if not isinstance(task, MultipleChoiceTask):
            raise ValueError(f"Expected MultipleChoiceTask, got {type(task).__name__}")
        if not isinstance(update_dto, MultipleChoiceTaskUpdate):
            raise ValueError(
                f"Expected MultipleChoiceTaskUpdate, got {type(update_dto).__name__}",
            )

        # Update base fields if provided
        if update_dto.prompt is not None:
            task.prompt = update_dto.prompt
        if update_dto.topic_detail is not None:
            task.topic_detail = update_dto.topic_detail

        # Update options (Replace-All semantics)
        if update_dto.options is not None:
            # Clear existing options (cascade delete-orphan handles DB cleanup)
            task.options.clear()

            # Add new options
            for opt_dto in update_dto.options:
                task.options.append(
                    TaskMultipleChoiceOption(
                        text=opt_dto.text,
                        is_correct=opt_dto.is_correct,
                        explanation=opt_dto.explanation,
                    ),
                )

        return task


class FreeTextTaskUpdateStrategy:
    """Update strategy for free text tasks."""

    task_type: TaskTypeKey = "free_text"

    def apply_update(self, task: Task, update_dto: TaskUpdateDto) -> Task:
        if not isinstance(task, FreeTextTask):
            raise ValueError(f"Expected FreeTextTask, got {type(task).__name__}")
        if not isinstance(update_dto, FreeTextTaskUpdate):
            raise ValueError(
                f"Expected FreeTextTaskUpdate, got {type(update_dto).__name__}",
            )

        # Update base fields if provided
        if update_dto.prompt is not None:
            task.prompt = update_dto.prompt
        if update_dto.topic_detail is not None:
            task.topic_detail = update_dto.topic_detail

        # Update type-specific field
        if update_dto.reference_answer is not None:
            task.reference_answer = update_dto.reference_answer

        return task


class ClozeTaskUpdateStrategy:
    """Update strategy for cloze tasks."""

    task_type: TaskTypeKey = "cloze"

    def apply_update(self, task: Task, update_dto: TaskUpdateDto) -> Task:
        if not isinstance(task, ClozeTask):
            raise ValueError(f"Expected ClozeTask, got {type(task).__name__}")
        if not isinstance(update_dto, ClozeTaskUpdate):
            raise ValueError(
                f"Expected ClozeTaskUpdate, got {type(update_dto).__name__}",
            )

        # Update base fields if provided
        if update_dto.prompt is not None:
            task.prompt = update_dto.prompt
        if update_dto.topic_detail is not None:
            task.topic_detail = update_dto.topic_detail

        # Update type-specific field
        if update_dto.template_text is not None:
            task.template_text = update_dto.template_text

        # Update blanks (Replace-All semantics)
        if update_dto.blanks is not None:
            # Clear existing blanks (cascade delete-orphan handles DB cleanup)
            task.blanks.clear()

            # Add new blanks
            for blank_dto in update_dto.blanks:
                task.blanks.append(
                    TaskClozeBlank(
                        position=blank_dto.position,
                        expected_value=blank_dto.expected_value,
                    ),
                )

        return task
