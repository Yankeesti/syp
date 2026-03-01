"""Tests for learning answer strategies."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.learning.models import (
    AnswerType,
    MultipleChoiceAnswer,
    FreeTextAnswer,
    ClozeAnswer,
)
from app.modules.learning.schemas.answer import (
    MultipleChoiceAnswerData,
    MultipleChoiceAnswerUpsert,
    FreeTextAnswerData,
    FreeTextAnswerUpsert,
    ClozeAnswerData,
    ClozeAnswerUpsert,
    ClozeItemData,
    ExistingMultipleChoiceAnswer,
    ExistingFreeTextAnswer,
    ExistingClozeAnswer,
)
from app.modules.learning.strategies.answer_mapping_strategy import (
    MultipleChoiceAnswerMappingStrategy,
    FreeTextAnswerMappingStrategy,
    ClozeAnswerMappingStrategy,
)
from app.modules.learning.strategies.answer_upsert_strategy import (
    MultipleChoiceAnswerUpsertStrategy,
    FreeTextAnswerUpsertStrategy,
    ClozeAnswerUpsertStrategy,
)


class TestAnswerMappingStrategies:
    """Mapping strategy tests."""

    def test_multiple_choice_maps_to_dto(self) -> None:
        task_id = uuid.uuid4()
        answer = MultipleChoiceAnswer(
            answer_id=uuid.uuid4(),
            attempt_id=uuid.uuid4(),
            task_id=task_id,
            type=AnswerType.MULTIPLE_CHOICE,
        )
        option_id_1 = uuid.uuid4()
        option_id_2 = uuid.uuid4()
        answer.selections = [
            MagicMock(option_id=option_id_1),
            MagicMock(option_id=option_id_2),
        ]

        strategy = MultipleChoiceAnswerMappingStrategy()
        dto = strategy.to_dto(answer)

        assert isinstance(dto, ExistingMultipleChoiceAnswer)
        assert dto.task_id == task_id
        assert dto.data.selected_option_ids == [option_id_1, option_id_2]

    def test_free_text_maps_to_dto(self) -> None:
        task_id = uuid.uuid4()
        answer = FreeTextAnswer(
            answer_id=uuid.uuid4(),
            attempt_id=uuid.uuid4(),
            task_id=task_id,
            type=AnswerType.FREE_TEXT,
            text_response="hello",
        )

        strategy = FreeTextAnswerMappingStrategy()
        dto = strategy.to_dto(answer)

        assert isinstance(dto, ExistingFreeTextAnswer)
        assert dto.task_id == task_id
        assert dto.data.text_response == "hello"

    def test_cloze_maps_to_dto(self) -> None:
        task_id = uuid.uuid4()
        answer = ClozeAnswer(
            answer_id=uuid.uuid4(),
            attempt_id=uuid.uuid4(),
            task_id=task_id,
            type=AnswerType.CLOZE,
        )
        blank_id_1 = uuid.uuid4()
        blank_id_2 = uuid.uuid4()
        answer.items = [
            MagicMock(blank_id=blank_id_1, provided_value="first"),
            MagicMock(blank_id=blank_id_2, provided_value="second"),
        ]

        strategy = ClozeAnswerMappingStrategy()
        dto = strategy.to_dto(answer)

        assert isinstance(dto, ExistingClozeAnswer)
        assert dto.task_id == task_id
        assert [item.blank_id for item in dto.data.provided_values] == [
            blank_id_1,
            blank_id_2,
        ]
        assert [item.value for item in dto.data.provided_values] == ["first", "second"]

    def test_mapping_strategy_rejects_wrong_model(self) -> None:
        answer = FreeTextAnswer(
            answer_id=uuid.uuid4(),
            attempt_id=uuid.uuid4(),
            task_id=uuid.uuid4(),
            type=AnswerType.FREE_TEXT,
            text_response="wrong",
        )

        strategy = MultipleChoiceAnswerMappingStrategy()
        with pytest.raises(ValueError):
            strategy.to_dto(answer)


class TestAnswerUpsertStrategies:
    """Upsert strategy tests."""

    @pytest.mark.asyncio
    async def test_multiple_choice_upsert_calls_repo(self) -> None:
        answer_repo = MagicMock()
        answer_repo.upsert_multiple_choice = AsyncMock(return_value=MagicMock())

        payload = MultipleChoiceAnswerUpsert(
            type="multiple_choice",
            data=MultipleChoiceAnswerData(
                selected_option_ids=[uuid.uuid4(), uuid.uuid4()],
            ),
        )
        attempt_id = uuid.uuid4()
        task_id = uuid.uuid4()

        strategy = MultipleChoiceAnswerUpsertStrategy()
        result = await strategy.upsert(answer_repo, attempt_id, task_id, payload)

        assert result is answer_repo.upsert_multiple_choice.return_value
        answer_repo.upsert_multiple_choice.assert_awaited_once_with(
            attempt_id,
            task_id,
            payload.data.selected_option_ids,
        )

    @pytest.mark.asyncio
    async def test_free_text_upsert_calls_repo(self) -> None:
        answer_repo = MagicMock()
        answer_repo.upsert_free_text = AsyncMock(return_value=MagicMock())

        payload = FreeTextAnswerUpsert(
            type="free_text",
            data=FreeTextAnswerData(text_response="hi"),
        )
        attempt_id = uuid.uuid4()
        task_id = uuid.uuid4()

        strategy = FreeTextAnswerUpsertStrategy()
        result = await strategy.upsert(answer_repo, attempt_id, task_id, payload)

        assert result is answer_repo.upsert_free_text.return_value
        answer_repo.upsert_free_text.assert_awaited_once_with(
            attempt_id,
            task_id,
            "hi",
        )

    @pytest.mark.asyncio
    async def test_cloze_upsert_calls_repo(self) -> None:
        answer_repo = MagicMock()
        answer_repo.upsert_cloze = AsyncMock(return_value=MagicMock())

        blank_id_1 = uuid.uuid4()
        blank_id_2 = uuid.uuid4()
        payload = ClozeAnswerUpsert(
            type="cloze",
            data=ClozeAnswerData(
                provided_values=[
                    ClozeItemData(blank_id=blank_id_1, value="one"),
                    ClozeItemData(blank_id=blank_id_2, value="two"),
                ],
            ),
        )
        attempt_id = uuid.uuid4()
        task_id = uuid.uuid4()

        strategy = ClozeAnswerUpsertStrategy()
        result = await strategy.upsert(answer_repo, attempt_id, task_id, payload)

        assert result is answer_repo.upsert_cloze.return_value
        answer_repo.upsert_cloze.assert_awaited_once_with(
            attempt_id,
            task_id,
            [
                {"blank_id": blank_id_1, "value": "one"},
                {"blank_id": blank_id_2, "value": "two"},
            ],
        )

    @pytest.mark.asyncio
    async def test_upsert_strategy_rejects_wrong_payload(self) -> None:
        answer_repo = MagicMock()
        payload = FreeTextAnswerUpsert(
            type="free_text",
            data=FreeTextAnswerData(text_response="wrong"),
        )

        strategy = MultipleChoiceAnswerUpsertStrategy()
        with pytest.raises(ValueError):
            await strategy.upsert(
                answer_repo,
                uuid.uuid4(),
                uuid.uuid4(),
                payload,
            )
