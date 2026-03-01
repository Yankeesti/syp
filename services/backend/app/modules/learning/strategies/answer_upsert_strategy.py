"""Answer upsert strategies for different answer types."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.modules.learning.models import Answer
from app.modules.learning.repositories import AnswerRepository
from app.modules.learning.schemas.answer import (
    AnswerUpsertRequest,
    MultipleChoiceAnswerUpsert,
    FreeTextAnswerUpsert,
    ClozeAnswerUpsert,
)
from app.modules.learning.strategies.answer_types import AnswerTypeKey


class AnswerUpsertStrategy(Protocol):
    """Upsert strategy for a specific answer type."""

    answer_type: AnswerTypeKey

    async def upsert(
        self,
        answer_repo: AnswerRepository,
        attempt_id: UUID,
        task_id: UUID,
        payload: AnswerUpsertRequest,
    ) -> Answer:
        """Upsert an answer and return the persisted model."""


class MultipleChoiceAnswerUpsertStrategy:
    answer_type: AnswerTypeKey = "multiple_choice"

    async def upsert(
        self,
        answer_repo: AnswerRepository,
        attempt_id: UUID,
        task_id: UUID,
        payload: AnswerUpsertRequest,
    ) -> Answer:
        if not isinstance(payload, MultipleChoiceAnswerUpsert):
            raise ValueError(f"Unexpected answer payload: {type(payload)}")

        return await answer_repo.upsert_multiple_choice(
            attempt_id,
            task_id,
            payload.data.selected_option_ids,
        )


class FreeTextAnswerUpsertStrategy:
    answer_type: AnswerTypeKey = "free_text"

    async def upsert(
        self,
        answer_repo: AnswerRepository,
        attempt_id: UUID,
        task_id: UUID,
        payload: AnswerUpsertRequest,
    ) -> Answer:
        if not isinstance(payload, FreeTextAnswerUpsert):
            raise ValueError(f"Unexpected answer payload: {type(payload)}")

        return await answer_repo.upsert_free_text(
            attempt_id,
            task_id,
            payload.data.text_response,
        )


class ClozeAnswerUpsertStrategy:
    answer_type: AnswerTypeKey = "cloze"

    async def upsert(
        self,
        answer_repo: AnswerRepository,
        attempt_id: UUID,
        task_id: UUID,
        payload: AnswerUpsertRequest,
    ) -> Answer:
        if not isinstance(payload, ClozeAnswerUpsert):
            raise ValueError(f"Unexpected answer payload: {type(payload)}")

        provided_values = [
            {"blank_id": item.blank_id, "value": item.value}
            for item in payload.data.provided_values
        ]

        return await answer_repo.upsert_cloze(
            attempt_id,
            task_id,
            provided_values,
        )
