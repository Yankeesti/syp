"""Answer mapping strategies for DTO conversion."""

from __future__ import annotations

from decimal import Decimal
from typing import Protocol

from app.modules.learning.models import (
    Answer,
    MultipleChoiceAnswer,
    FreeTextAnswer,
    ClozeAnswer,
)
from app.modules.learning.schemas.answer import (
    ExistingAnswerDTO,
    ExistingMultipleChoiceAnswer,
    MultipleChoiceAnswerData,
    ExistingFreeTextAnswer,
    FreeTextAnswerData,
    ExistingClozeAnswer,
    ClozeAnswerData,
    ClozeItemData,
)
from app.modules.learning.strategies.answer_types import AnswerTypeKey
from app.shared.utils import quantize_percent


def _to_percentage(value: Decimal | None) -> float | None:
    quantized = quantize_percent(value)
    return float(quantized) if quantized is not None else None


class AnswerMappingStrategy(Protocol):
    """Mapping strategy for a specific answer type."""

    answer_type: AnswerTypeKey

    def to_dto(self, answer: Answer) -> ExistingAnswerDTO:
        """Map an answer model to its output DTO."""


class MultipleChoiceAnswerMappingStrategy:
    answer_type: AnswerTypeKey = "multiple_choice"

    def to_dto(self, answer: Answer) -> ExistingAnswerDTO:
        if not isinstance(answer, MultipleChoiceAnswer):
            raise ValueError(f"Unexpected answer model: {type(answer)}")

        return ExistingMultipleChoiceAnswer(
            task_id=answer.task_id,
            type="multiple_choice",
            percentage_correct=_to_percentage(answer.percentage_correct),
            data=MultipleChoiceAnswerData(
                selected_option_ids=[s.option_id for s in answer.selections],
            ),
        )


class FreeTextAnswerMappingStrategy:
    answer_type: AnswerTypeKey = "free_text"

    def to_dto(self, answer: Answer) -> ExistingAnswerDTO:
        if not isinstance(answer, FreeTextAnswer):
            raise ValueError(f"Unexpected answer model: {type(answer)}")

        return ExistingFreeTextAnswer(
            task_id=answer.task_id,
            type="free_text",
            percentage_correct=_to_percentage(answer.percentage_correct),
            data=FreeTextAnswerData(text_response=answer.text_response),
        )


class ClozeAnswerMappingStrategy:
    answer_type: AnswerTypeKey = "cloze"

    def to_dto(self, answer: Answer) -> ExistingAnswerDTO:
        if not isinstance(answer, ClozeAnswer):
            raise ValueError(f"Unexpected answer model: {type(answer)}")

        return ExistingClozeAnswer(
            task_id=answer.task_id,
            type="cloze",
            percentage_correct=_to_percentage(answer.percentage_correct),
            data=ClozeAnswerData(
                provided_values=[
                    ClozeItemData(blank_id=item.blank_id, value=item.provided_value)
                    for item in answer.items
                ],
            ),
        )
