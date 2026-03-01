"""Pydantic schemas for Attempt DTOs."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.modules.learning.schemas.answer import ExistingAnswerDTO
from app.modules.learning.models.attempt import AttemptStatus


class AttemptSummaryResponse(BaseModel):
    """Response for POST /learning/quizzes/{quiz_id}/attempts."""

    attempt_id: UUID
    quiz_id: UUID
    status: AttemptStatus
    started_at: datetime
    existing_answers: list[ExistingAnswerDTO] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class AttemptListItem(BaseModel):
    """Single attempt item in list response."""

    attempt_id: UUID
    quiz_id: UUID
    status: AttemptStatus
    started_at: datetime
    evaluated_at: datetime | None = None
    total_percentage: float | None = None

    model_config = {"from_attributes": True}


class AttemptLinks(BaseModel):
    """HAL-style links for attempt responses."""

    tasks: str


class AttemptDetailResponse(BaseModel):
    """Response for GET /learning/attempts/{attempt_id}."""

    attempt_id: UUID
    quiz_id: UUID
    status: AttemptStatus
    started_at: datetime
    evaluated_at: datetime | None = None
    total_percentage: float | None = None
    answers: list[ExistingAnswerDTO] = Field(default_factory=list)
    links: AttemptLinks | None = Field(default=None, serialization_alias="_links")

    model_config = {"from_attributes": True, "populate_by_name": True}
