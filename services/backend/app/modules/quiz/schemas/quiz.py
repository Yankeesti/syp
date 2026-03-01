from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.modules.quiz.models.quiz import QuizState, QuizStatus
from app.modules.quiz.schemas.task import Task


class QuizListItem(BaseModel):

    quiz_id: UUID
    title: str
    topic: str | None
    state: QuizState
    status: QuizStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class QuizCreateResponse(BaseModel):

    quiz_id: UUID
    status: QuizStatus


class QuizDetailResponse(BaseModel):

    quiz_id: UUID
    title: str
    topic: str | None
    status: QuizStatus
    state: QuizState
    created_by: UUID
    created_at: datetime
    tasks: list[Task]

    model_config = {"from_attributes": True}
