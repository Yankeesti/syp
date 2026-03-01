"""Task type strategies for mapping between DTOs and models."""

from __future__ import annotations

from typing import Literal, Protocol, cast
from uuid import UUID

from app.modules.quiz.models.task import (
    Task,
    TaskType,
    MultipleChoiceTask,
    TaskMultipleChoiceOption,
    FreeTextTask,
    ClozeTask,
    TaskClozeBlank,
)
from app.modules.quiz.schemas import (
    TaskDetailDto,
    TaskUpsertDto,
    MultipleChoiceTaskCreate,
    FreeTextTaskCreate,
    ClozeTaskCreate,
    MultipleChoiceTaskResponse,
    MultipleChoiceOptionResponse,
    FreeTextTaskResponse,
    ClozeTaskResponse,
    ClozeBlankResponse,
)

TaskTypeKey = Literal["multiple_choice", "free_text", "cloze"]


class TaskMappingStrategy(Protocol):
    """Mapping strategy for a specific task type."""

    task_type: TaskTypeKey

    def build_model(
        self,
        quiz_id: UUID,
        quiz_version_id: UUID,
        task_input: TaskUpsertDto,
        order_index: int,
    ) -> Task:
        """Build a task model from input DTO."""

    def to_dto(self, task: Task) -> TaskDetailDto:
        """Map a task model to its output DTO."""


def normalize_task_type(value: TaskType | str) -> TaskTypeKey:
    """Normalize a task type enum/string to a registry key."""
    if isinstance(value, TaskType):
        return cast(TaskTypeKey, value.value)
    return cast(TaskTypeKey, value)


class MultipleChoiceTaskMappingStrategy:
    task_type: TaskTypeKey = "multiple_choice"

    def build_model(
        self,
        quiz_id: UUID,
        quiz_version_id: UUID,
        task_input: TaskUpsertDto,
        order_index: int,
    ) -> Task:
        if not isinstance(task_input, MultipleChoiceTaskCreate):
            raise ValueError(f"Unexpected task input: {type(task_input)}")

        options = [
            TaskMultipleChoiceOption(
                text=opt.text,
                is_correct=opt.is_correct,
                explanation=opt.explanation,
            )
            for opt in task_input.options
        ]

        return MultipleChoiceTask(
            quiz_id=quiz_id,
            quiz_version_id=quiz_version_id,
            prompt=task_input.prompt,
            topic_detail=task_input.topic_detail,
            order_index=order_index,
            options=options,
        )

    def to_dto(self, task: Task) -> TaskDetailDto:
        if not isinstance(task, MultipleChoiceTask):
            raise ValueError(f"Unexpected task model: {type(task)}")

        options = [
            MultipleChoiceOptionResponse(
                option_id=option.option_id,
                text=option.text,
                is_correct=option.is_correct,
                explanation=option.explanation,
            )
            for option in (task.options or [])
        ]

        return MultipleChoiceTaskResponse(
            task_id=task.task_id,
            quiz_id=task.quiz_id,
            prompt=task.prompt,
            topic_detail=task.topic_detail,
            order_index=task.order_index,
            type="multiple_choice",
            options=options,
        )


class FreeTextTaskMappingStrategy:
    task_type: TaskTypeKey = "free_text"

    def build_model(
        self,
        quiz_id: UUID,
        quiz_version_id: UUID,
        task_input: TaskUpsertDto,
        order_index: int,
    ) -> Task:
        if not isinstance(task_input, FreeTextTaskCreate):
            raise ValueError(f"Unexpected task input: {type(task_input)}")

        return FreeTextTask(
            quiz_id=quiz_id,
            quiz_version_id=quiz_version_id,
            prompt=task_input.prompt,
            topic_detail=task_input.topic_detail,
            order_index=order_index,
            reference_answer=task_input.reference_answer,
        )

    def to_dto(self, task: Task) -> TaskDetailDto:
        if not isinstance(task, FreeTextTask):
            raise ValueError(f"Unexpected task model: {type(task)}")

        return FreeTextTaskResponse(
            task_id=task.task_id,
            quiz_id=task.quiz_id,
            prompt=task.prompt,
            topic_detail=task.topic_detail,
            order_index=task.order_index,
            type="free_text",
            reference_answer=task.reference_answer,
        )


class ClozeTaskMappingStrategy:
    task_type: TaskTypeKey = "cloze"

    def build_model(
        self,
        quiz_id: UUID,
        quiz_version_id: UUID,
        task_input: TaskUpsertDto,
        order_index: int,
    ) -> Task:
        if not isinstance(task_input, ClozeTaskCreate):
            raise ValueError(f"Unexpected task input: {type(task_input)}")

        blanks = [
            TaskClozeBlank(
                position=blank.position,
                expected_value=blank.expected_value,
            )
            for blank in task_input.blanks
        ]

        return ClozeTask(
            quiz_id=quiz_id,
            quiz_version_id=quiz_version_id,
            prompt=task_input.prompt,
            topic_detail=task_input.topic_detail,
            order_index=order_index,
            template_text=task_input.template_text,
            blanks=blanks,
        )

    def to_dto(self, task: Task) -> TaskDetailDto:
        if not isinstance(task, ClozeTask):
            raise ValueError(f"Unexpected task model: {type(task)}")

        blanks = [
            ClozeBlankResponse(
                blank_id=blank.blank_id,
                position=blank.position,
                expected_value=blank.expected_value,
            )
            for blank in (task.blanks or [])
        ]

        return ClozeTaskResponse(
            task_id=task.task_id,
            quiz_id=task.quiz_id,
            prompt=task.prompt,
            topic_detail=task.topic_detail,
            order_index=task.order_index,
            type="cloze",
            template_text=task.template_text,
            blanks=blanks,
        )
