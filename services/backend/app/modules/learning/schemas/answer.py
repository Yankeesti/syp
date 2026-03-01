"""Pydantic schemas for Answer DTOs with discriminated unions.

These schemas represent the API request/response format for answers.
Uses discriminated unions to handle polymorphic answer types.
"""

from datetime import datetime
from typing import Annotated, Literal, Union
from uuid import UUID

from pydantic import BaseModel, Field


# === Data Payloads for Request/Response ===


class MultipleChoiceAnswerData(BaseModel):
    """Data payload for multiple choice answers."""

    selected_option_ids: list[UUID]


class FreeTextAnswerData(BaseModel):
    """Data payload for free text answers."""

    text_response: str


class ClozeItemData(BaseModel):
    """Single blank fill for cloze answers."""

    blank_id: UUID
    value: str


class ClozeAnswerData(BaseModel):
    """Data payload for cloze answers."""

    provided_values: list[ClozeItemData]


# === Upsert Request (Discriminated Union) ===


class MultipleChoiceAnswerUpsert(BaseModel):
    """Upsert request for multiple choice answer."""

    type: Literal["multiple_choice"]
    data: MultipleChoiceAnswerData


class FreeTextAnswerUpsert(BaseModel):
    """Upsert request for free text answer."""

    type: Literal["free_text"]
    data: FreeTextAnswerData


class ClozeAnswerUpsert(BaseModel):
    """Upsert request for cloze answer."""

    type: Literal["cloze"]
    data: ClozeAnswerData


# Discriminated Union: Pydantic automatically selects the correct upsert class
# based on the "type" field (e.g., "multiple_choice" → MultipleChoiceAnswerUpsert).
# This enables type-safe polymorphism and clean OpenAPI schema generation.
AnswerUpsertRequest = Annotated[
    Union[MultipleChoiceAnswerUpsert, FreeTextAnswerUpsert, ClozeAnswerUpsert],
    Field(discriminator="type"),
]


# === Response for Saved Answer ===


class AnswerSavedResponse(BaseModel):
    """Response for PUT /learning/attempts/{attempt_id}/answers/{task_id}."""

    answer_id: UUID
    task_id: UUID
    saved_at: datetime


# === Free Text Correctness Request ===


class FreeTextCorrectnessRequest(BaseModel):
    """Request for PATCH .../free-text-correctness."""

    is_correct: bool


# === Existing Answer DTOs (for AttemptSummaryResponse) ===


class ExistingMultipleChoiceAnswer(BaseModel):
    """Existing multiple choice answer DTO."""

    task_id: UUID
    type: Literal["multiple_choice"]
    percentage_correct: float | None = None
    data: MultipleChoiceAnswerData

    model_config = {"from_attributes": True}


class ExistingFreeTextAnswer(BaseModel):
    """Existing free text answer DTO."""

    task_id: UUID
    type: Literal["free_text"]
    percentage_correct: float | None = None
    data: FreeTextAnswerData

    model_config = {"from_attributes": True}


class ExistingClozeAnswer(BaseModel):
    """Existing cloze answer DTO."""

    task_id: UUID
    type: Literal["cloze"]
    percentage_correct: float | None = None
    data: ClozeAnswerData

    model_config = {"from_attributes": True}


# Discriminated Union for existing answers returned in AttemptSummaryResponse.
# Enables type-safe handling of different answer types.
ExistingAnswerDTO = Annotated[
    Union[ExistingMultipleChoiceAnswer, ExistingFreeTextAnswer, ExistingClozeAnswer],
    Field(discriminator="type"),
]
