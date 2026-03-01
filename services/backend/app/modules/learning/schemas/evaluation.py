"""Pydantic schemas for Evaluation DTOs with discriminated unions.

These schemas represent the API response format for attempt evaluations.
Uses discriminated unions to handle polymorphic answer detail types.
"""

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal, Union
from uuid import UUID

from pydantic import BaseModel, Field


# === Answer Detail DTOs for Evaluation Response ===


class MultipleChoiceAnswerDetail(BaseModel):
    """Answer detail for multiple choice task evaluation."""

    task_id: UUID
    type: Literal["multiple_choice"]
    percentage_correct: Decimal

    model_config = {"from_attributes": True}


class FreeTextAnswerDetail(BaseModel):
    """Answer detail for free text task evaluation."""

    task_id: UUID
    type: Literal["free_text"]
    percentage_correct: Decimal

    model_config = {"from_attributes": True}


class ClozeAnswerDetail(BaseModel):
    """Answer detail for cloze task evaluation."""

    task_id: UUID
    type: Literal["cloze"]
    percentage_correct: Decimal

    model_config = {"from_attributes": True}


# Discriminated Union: Pydantic automatically selects the correct detail class
# based on the "type" field (e.g., "multiple_choice" → MultipleChoiceAnswerDetail).
# This enables type-safe polymorphism and clean OpenAPI schema generation.
AnswerDetailDTO = Annotated[
    Union[MultipleChoiceAnswerDetail, FreeTextAnswerDetail, ClozeAnswerDetail],
    Field(discriminator="type"),
]


class EvaluationResponse(BaseModel):
    """Response for POST /learning/attempts/{attempt_id}/evaluation."""

    attempt_id: UUID
    quiz_id: UUID
    total_percentage: Decimal
    evaluated_at: datetime
    answer_details: list[AnswerDetailDTO]

    model_config = {"from_attributes": True}
