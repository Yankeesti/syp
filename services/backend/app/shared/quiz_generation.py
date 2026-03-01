"""Shared DTOs for quiz generation."""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field

from app.shared.enums import TaskType


# =============================================================================
# Task Creation Schemas (LLM output + quiz creation)
# =============================================================================


class MultipleChoiceOptionCreate(BaseModel):
    """Multiple choice option for task creation."""

    text: str
    is_correct: bool
    explanation: str | None = None


class MultipleChoiceTaskCreate(BaseModel):
    """Multiple choice task creation schema."""

    type: Literal["multiple_choice"]
    prompt: str
    topic_detail: str
    options: list[MultipleChoiceOptionCreate]


class FreeTextTaskCreate(BaseModel):
    """Free text task creation schema."""

    type: Literal["free_text"]
    prompt: str
    topic_detail: str
    reference_answer: str


class ClozeBlankCreate(BaseModel):
    """Cloze blank for task creation."""

    position: int
    expected_value: str


class ClozeTaskCreate(BaseModel):
    """Cloze (fill-in-the-blank) task creation schema."""

    type: Literal["cloze"]
    prompt: str
    topic_detail: str
    template_text: str
    blanks: list[ClozeBlankCreate]


TaskUpsertDto = Annotated[
    Union[MultipleChoiceTaskCreate, FreeTextTaskCreate, ClozeTaskCreate],
    Field(discriminator="type"),
]


# =============================================================================
# Quiz Generation Schemas
# =============================================================================


class QuizGenerationSpec(BaseModel):
    """Input spec for quiz generation."""

    task_types: list[TaskType]
    user_description: str | None = None
    file_content: bytes | None = None


class QuizUpsertDto(BaseModel):
    """Complete quiz upsert schema including metadata and tasks."""

    title: str
    topic: str
    tasks: list[TaskUpsertDto]


__all__ = [
    "ClozeBlankCreate",
    "ClozeTaskCreate",
    "FreeTextTaskCreate",
    "MultipleChoiceOptionCreate",
    "MultipleChoiceTaskCreate",
    "QuizGenerationSpec",
    "QuizUpsertDto",
    "TaskUpsertDto",
]
