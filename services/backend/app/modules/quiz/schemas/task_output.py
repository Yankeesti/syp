"""Pydantic schemas for Task DTOs with discriminated unions.

These schemas represent the API response format for tasks.
Uses discriminated unions to handle polymorphic task types.
"""

from typing import Annotated, Literal, Union
from uuid import UUID

from pydantic import BaseModel, Field


class TaskBase(BaseModel):
    """Base fields shared by all task types."""

    task_id: UUID
    quiz_id: UUID
    prompt: str
    topic_detail: str
    order_index: int

    model_config = {"from_attributes": True}


class MultipleChoiceOptionResponse(BaseModel):
    """Response DTO for a multiple choice option."""

    option_id: UUID
    text: str
    is_correct: bool
    explanation: str | None = None

    model_config = {"from_attributes": True}


class MultipleChoiceTaskResponse(TaskBase):
    """Response DTO for multiple choice task."""

    type: Literal["multiple_choice"]
    options: list[MultipleChoiceOptionResponse]


class FreeTextTaskResponse(TaskBase):
    """Response DTO for free text task."""

    type: Literal["free_text"]
    reference_answer: str


class ClozeBlankResponse(BaseModel):
    """Response DTO for a cloze blank."""

    blank_id: UUID
    position: int
    expected_value: str

    model_config = {"from_attributes": True}


class ClozeTaskResponse(TaskBase):
    """Response DTO for cloze task."""

    type: Literal["cloze"]
    template_text: str
    blanks: list[ClozeBlankResponse]


# Discriminated Union: Pydantic automatically selects the correct DTO class
# based on the "type" field (e.g., "multiple_choice" → MultipleChoiceTaskResponse).
# This enables type-safe polymorphism and clean OpenAPI schema generation.
TaskDetailDto = Annotated[
    Union[MultipleChoiceTaskResponse, FreeTextTaskResponse, ClozeTaskResponse],
    Field(discriminator="type"),
]
