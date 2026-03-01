"""Learning module Pydantic schemas."""

from app.modules.learning.schemas.answer import (
    AnswerSavedResponse,
    AnswerUpsertRequest,
    ClozeAnswerData,
    ClozeItemData,
    ExistingAnswerDTO,
    FreeTextAnswerData,
    FreeTextCorrectnessRequest,
    MultipleChoiceAnswerData,
)
from app.modules.learning.schemas.attempt import (
    AttemptLinks,
    AttemptListItem,
    AttemptDetailResponse,
    AttemptSummaryResponse,
)
from app.modules.learning.models.attempt import AttemptStatus
from app.modules.learning.schemas.evaluation import (
    AnswerDetailDTO,
    EvaluationResponse,
)

__all__ = [
    # Attempt schemas
    "AttemptLinks",
    "AttemptListItem",
    "AttemptDetailResponse",
    "AttemptSummaryResponse",
    "AttemptStatus",
    # Answer schemas
    "AnswerUpsertRequest",
    "AnswerSavedResponse",
    "FreeTextCorrectnessRequest",
    "MultipleChoiceAnswerData",
    "FreeTextAnswerData",
    "ClozeAnswerData",
    "ClozeItemData",
    "ExistingAnswerDTO",
    # Evaluation schemas
    "EvaluationResponse",
    "AnswerDetailDTO",
]
