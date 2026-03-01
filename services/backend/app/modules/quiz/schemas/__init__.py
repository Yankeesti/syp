"""Quiz module Pydantic schemas for API requests/responses."""

from app.modules.quiz.schemas.quiz_input import (
    QuizGenerationSpec,
    QuizUpsertDto,
)
from app.modules.quiz.schemas.share_link import (
    ShareLinkCreateRequest,
    ShareLinkDto,
    ShareLinkInfoDto,
)
from app.modules.quiz.schemas.quiz_output import (
    QuizCreationStatus,
    QuizDetailDto,
    QuizSummaryDto,
    QuizAccessDto,
)
from app.modules.quiz.schemas.edit_session import (
    QuizEditSessionStartResponse,
    QuizEditSessionCommitRequest,
    QuizEditSessionCommitResponse,
    QuizEditSessionAbortRequest,
)
from app.modules.quiz.schemas.requests import QuizCreateRequest
from app.modules.quiz.schemas.task_input import (
    ClozeBlankCreate,
    ClozeTaskCreate,
    FreeTextTaskCreate,
    MultipleChoiceOptionCreate,
    MultipleChoiceTaskCreate,
    TaskUpsertDto,
    # Update schemas
    ClozeBlankUpdate,
    ClozeTaskUpdate,
    FreeTextTaskUpdate,
    MultipleChoiceOptionUpdate,
    MultipleChoiceTaskUpdate,
    TaskUpdateDto,
)
from app.modules.quiz.schemas.task_output import (
    ClozeBlankResponse,
    ClozeTaskResponse,
    FreeTextTaskResponse,
    MultipleChoiceOptionResponse,
    MultipleChoiceTaskResponse,
    TaskBase,
    TaskDetailDto,
)

__all__ = [
    # Quiz request schemas
    "QuizCreateRequest",
    # Quiz input schemas
    "QuizGenerationSpec",
    "QuizUpsertDto",
    # Quiz output schemas
    "QuizSummaryDto",
    "QuizCreationStatus",
    "QuizDetailDto",
    "QuizAccessDto",
    # Edit session schemas
    "QuizEditSessionStartResponse",
    "QuizEditSessionCommitRequest",
    "QuizEditSessionCommitResponse",
    "QuizEditSessionAbortRequest",
    # Share link schemas
    "ShareLinkCreateRequest",
    "ShareLinkDto",
    "ShareLinkInfoDto",
    # Task creation schemas
    "TaskUpsertDto",
    "MultipleChoiceTaskCreate",
    "MultipleChoiceOptionCreate",
    "FreeTextTaskCreate",
    "ClozeTaskCreate",
    "ClozeBlankCreate",
    # Task update schemas
    "TaskUpdateDto",
    "MultipleChoiceTaskUpdate",
    "MultipleChoiceOptionUpdate",
    "FreeTextTaskUpdate",
    "ClozeTaskUpdate",
    "ClozeBlankUpdate",
    # Task output schemas
    "TaskBase",
    "MultipleChoiceOptionResponse",
    "MultipleChoiceTaskResponse",
    "FreeTextTaskResponse",
    "ClozeBlankResponse",
    "ClozeTaskResponse",
    "TaskDetailDto",
]
