"""Schemas for quiz edit session endpoints."""

from uuid import UUID

from pydantic import BaseModel

from app.modules.quiz.schemas.quiz_output import QuizDetailDto


class QuizEditSessionStartResponse(BaseModel):
    """Response for starting an edit session."""

    edit_session_id: UUID
    quiz: QuizDetailDto


class QuizEditSessionCommitRequest(BaseModel):
    """Request body for committing an edit session."""

    edit_session_id: UUID


class QuizEditSessionCommitResponse(BaseModel):
    """Response for committing an edit session."""

    quiz_id: UUID
    current_version_id: UUID
    version_number: int


class QuizEditSessionAbortRequest(BaseModel):
    """Request body for aborting an edit session."""

    edit_session_id: UUID
