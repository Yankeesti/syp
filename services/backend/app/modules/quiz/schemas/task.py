from typing import Annotated, Literal, Union
from uuid import UUID

from pydantic import BaseModel, Field


class MultipleChoiceOptionDTO(BaseModel):

    option_id: UUID
    text: str
    is_correct: bool
    explanation: str | None = None

    model_config = {"from_attributes": True}


class TaskBase(BaseModel):

    task_id: UUID
    quiz_id: UUID
    prompt: str
    topic_detail: str
    order_index: int

    model_config = {"from_attributes": True}


class MultipleChoiceTaskDTO(TaskBase):

    type: Literal["multiple_choice"]
    options: list[MultipleChoiceOptionDTO]


class FreeTextTaskDTO(TaskBase):

    type: Literal["free_text"]
    reference_answer: str


class ClozeBlankDTO(BaseModel):

    blank_id: UUID
    position: int
    expected_value: str

    model_config = {"from_attributes": True}


class ClozeTaskDTO(TaskBase):

    type: Literal["cloze"]
    template_text: str
    blanks: list[ClozeBlankDTO]


# Discriminated Union: Pydantic automatically selects the correct DTO class
# based on the "type" field (e.g., "multiple_choice" → MultipleChoiceTaskDTO).
# This enables type-safe polymorphism and clean OpenAPI schema generation.
Task = Annotated[
    Union[MultipleChoiceTaskDTO, FreeTextTaskDTO, ClozeTaskDTO],
    Field(discriminator="type"),
]

TaskDTO = Task  # Alias for naming consistency with other DTOs
