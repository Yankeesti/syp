"""Pydantic schemas for task creation and update (input DTOs).

These schemas define the data structure for creating and updating tasks
without database-specific fields (like IDs, timestamps).

Used by:
- API endpoints for manual task creation and update
- Import functionality

Note: Task creation DTOs live in app.shared.quiz_generation and are
re-exported here for quiz module convenience.
"""

from typing import Annotated, Literal, Union
from uuid import UUID

from pydantic import BaseModel, Field

from app.shared.quiz_generation import (
    ClozeBlankCreate,
    ClozeTaskCreate,
    FreeTextTaskCreate,
    MultipleChoiceOptionCreate,
    MultipleChoiceTaskCreate,
    TaskUpsertDto,
)

# =============================================================================
# Task Update Schemas
# =============================================================================


class MultipleChoiceOptionUpdate(BaseModel):
    """Multiple choice option for task update.

    Uses Replace-All semantics: the entire options list is replaced.
    option_id is optional - if provided, it's kept for reference but all
    options are recreated.
    """

    option_id: UUID | None = None
    text: str
    is_correct: bool
    explanation: str | None = None


class MultipleChoiceTaskUpdate(BaseModel):
    """Multiple choice task update schema.

    All fields except 'type' are optional for partial updates.
    If 'options' is provided, all existing options are replaced (Replace-All).
    """

    type: Literal["multiple_choice"]
    prompt: str | None = None
    topic_detail: str | None = None
    options: list[MultipleChoiceOptionUpdate] | None = None


class FreeTextTaskUpdate(BaseModel):
    """Free text task update schema.

    All fields except 'type' are optional for partial updates.
    """

    type: Literal["free_text"]
    prompt: str | None = None
    topic_detail: str | None = None
    reference_answer: str | None = None


class ClozeBlankUpdate(BaseModel):
    """Cloze blank for task update.

    Uses Replace-All semantics: the entire blanks list is replaced.
    blank_id is optional - if provided, it's kept for reference but all
    blanks are recreated.
    """

    blank_id: UUID | None = None
    position: int
    expected_value: str


class ClozeTaskUpdate(BaseModel):
    """Cloze task update schema.

    All fields except 'type' are optional for partial updates.
    If 'blanks' is provided, all existing blanks are replaced (Replace-All).
    """

    type: Literal["cloze"]
    prompt: str | None = None
    topic_detail: str | None = None
    template_text: str | None = None
    blanks: list[ClozeBlankUpdate] | None = None


# Discriminated Union for task updates
TaskUpdateDto = Annotated[
    Union[MultipleChoiceTaskUpdate, FreeTextTaskUpdate, ClozeTaskUpdate],
    Field(discriminator="type"),
]
