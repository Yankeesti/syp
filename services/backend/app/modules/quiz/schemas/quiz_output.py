"""Pydantic schemas for Quiz response DTOs.

These schemas represent the API response formats for quiz endpoints.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.modules.quiz.models.quiz import QuizState, QuizStatus
from app.modules.quiz.models.quiz_ownership import OwnershipRole
from app.modules.quiz.models.task import TaskType
from app.modules.quiz.schemas.task_output import TaskDetailDto


class QuizSummaryDto(BaseModel):
    """DTO for a single quiz in list response."""

    quiz_id: UUID
    title: str
    topic: str | None
    state: QuizState
    status: QuizStatus
    role: OwnershipRole
    created_at: datetime
    question_count: int
    question_types: list[TaskType]

    model_config = {"from_attributes": True}


class QuizCreationStatus(BaseModel):
    """Response model for POST /quizzes - 202 Accepted."""

    quiz_id: UUID
    status: QuizStatus


class QuizDetailDto(BaseModel):
    """Response model for GET /quizzes/{id} - full quiz with tasks."""

    quiz_id: UUID
    title: str
    topic: str | None
    status: QuizStatus
    state: QuizState
    created_by: UUID
    created_at: datetime
    tasks: list[TaskDetailDto]

    model_config = {"from_attributes": True}


class QuizAccessDto(BaseModel):
    """DTO for access-checked quiz metadata used by other modules."""

    quiz_id: UUID
    status: QuizStatus
    state: QuizState

    model_config = {"from_attributes": True}
