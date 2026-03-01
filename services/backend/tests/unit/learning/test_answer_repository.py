"""Tests for AnswerRepository."""

import uuid
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.learning.models import (
    Attempt,
    AttemptStatus,
    MultipleChoiceAnswer,
    FreeTextAnswer,
    ClozeAnswer,
    AnswerType,
)
from app.modules.learning.repositories.attempt_repository import AttemptRepository
from app.modules.learning.exceptions import AnswerTypeMismatchException
from app.modules.learning.repositories.answer_repository import AnswerRepository


pytestmark = pytest.mark.unit


class TestAnswerRepository:
    """Tests for AnswerRepository."""

    @pytest.fixture
    def attempt_repo(self, db_session: AsyncSession) -> AttemptRepository:
        """Create AttemptRepository instance."""
        return AttemptRepository(db_session)

    @pytest.fixture
    def repository(self, db_session: AsyncSession) -> AnswerRepository:
        """Create AnswerRepository instance."""
        return AnswerRepository(db_session)

    @pytest.fixture
    async def sample_attempt(
        self,
        attempt_repo: AttemptRepository,
        db_session: AsyncSession,
    ) -> Attempt:
        """Create a sample attempt for testing."""
        attempt = await attempt_repo.create_attempt(uuid.uuid4(), uuid.uuid4())
        await db_session.commit()
        return attempt

    @pytest.fixture
    def task_id(self):
        """Create a task ID for testing."""
        return uuid.uuid4()

    # ==================== Multiple Choice Tests ====================

    async def test_upsert_multiple_choice_create(
        self,
        repository: AnswerRepository,
        sample_attempt: Attempt,
        task_id: uuid.UUID,
        db_session: AsyncSession,
    ):
        """Test creating a multiple choice answer."""
        # Arrange
        option_ids = [uuid.uuid4(), uuid.uuid4()]

        # Act
        answer = await repository.upsert_multiple_choice(
            sample_attempt.attempt_id,
            task_id,
            option_ids,
        )
        await db_session.commit()

        # Assert
        assert isinstance(answer, MultipleChoiceAnswer)
        assert answer.task_id == task_id
        assert answer.attempt_id == sample_attempt.attempt_id
        assert len(answer.selections) == 2
        selection_option_ids = {s.option_id for s in answer.selections}
        assert selection_option_ids == set(option_ids)

    async def test_upsert_multiple_choice_update(
        self,
        repository: AnswerRepository,
        sample_attempt: Attempt,
        task_id: uuid.UUID,
        db_session: AsyncSession,
    ):
        """Test updating multiple choice selections (idempotent)."""
        # Arrange
        opt1, opt2, opt3 = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()

        # Act - First upsert
        await repository.upsert_multiple_choice(
            sample_attempt.attempt_id,
            task_id,
            [opt1, opt2],
        )
        await db_session.commit()

        # Act - Second upsert with different selections
        answer = await repository.upsert_multiple_choice(
            sample_attempt.attempt_id,
            task_id,
            [opt2, opt3],
        )
        await db_session.commit()

        # Assert - Only opt2 and opt3 should be selected
        selection_ids = {s.option_id for s in answer.selections}
        assert selection_ids == {opt2, opt3}

    async def test_upsert_multiple_choice_remove_all(
        self,
        repository: AnswerRepository,
        sample_attempt: Attempt,
        task_id: uuid.UUID,
        db_session: AsyncSession,
    ):
        """Test removing all selections from a multiple choice answer."""
        # Arrange
        opt1, opt2 = uuid.uuid4(), uuid.uuid4()
        await repository.upsert_multiple_choice(
            sample_attempt.attempt_id,
            task_id,
            [opt1, opt2],
        )
        await db_session.commit()

        # Act - Upsert with empty list
        answer = await repository.upsert_multiple_choice(
            sample_attempt.attempt_id,
            task_id,
            [],
        )
        await db_session.commit()

        # Assert - No selections
        assert len(answer.selections) == 0

    async def test_upsert_multiple_choice_type_mismatch(
        self,
        repository: AnswerRepository,
        sample_attempt: Attempt,
        task_id: uuid.UUID,
        db_session: AsyncSession,
    ):
        """Test that updating wrong type raises ValueError."""
        # Arrange - Create free text answer first
        await repository.upsert_free_text(
            sample_attempt.attempt_id,
            task_id,
            "Some text",
        )
        await db_session.commit()

        # Act & Assert - Try to upsert as multiple choice
        with pytest.raises(AnswerTypeMismatchException):
            await repository.upsert_multiple_choice(
                sample_attempt.attempt_id,
                task_id,
                [uuid.uuid4()],
            )

    # ==================== Free Text Tests ====================

    async def test_upsert_free_text_create(
        self,
        repository: AnswerRepository,
        sample_attempt: Attempt,
        task_id: uuid.UUID,
        db_session: AsyncSession,
    ):
        """Test creating a free text answer."""
        # Arrange
        text = "My answer text"

        # Act
        answer = await repository.upsert_free_text(
            sample_attempt.attempt_id,
            task_id,
            text,
        )
        await db_session.commit()

        # Assert
        assert isinstance(answer, FreeTextAnswer)
        assert answer.text_response == text
        assert answer.task_id == task_id
        assert answer.attempt_id == sample_attempt.attempt_id

    async def test_upsert_free_text_update(
        self,
        repository: AnswerRepository,
        sample_attempt: Attempt,
        task_id: uuid.UUID,
        db_session: AsyncSession,
    ):
        """Test updating free text answer."""
        # Arrange - Create initial answer
        await repository.upsert_free_text(
            sample_attempt.attempt_id,
            task_id,
            "First answer",
        )
        await db_session.commit()

        # Act - Update with new text
        answer = await repository.upsert_free_text(
            sample_attempt.attempt_id,
            task_id,
            "Updated answer",
        )
        await db_session.commit()

        # Assert
        assert answer.text_response == "Updated answer"

    async def test_upsert_free_text_empty_string(
        self,
        repository: AnswerRepository,
        sample_attempt: Attempt,
        task_id: uuid.UUID,
        db_session: AsyncSession,
    ):
        """Test that empty string is valid for free text."""
        # Act
        answer = await repository.upsert_free_text(
            sample_attempt.attempt_id,
            task_id,
            "",
        )
        await db_session.commit()

        # Assert
        assert answer.text_response == ""

    async def test_upsert_free_text_type_mismatch(
        self,
        repository: AnswerRepository,
        sample_attempt: Attempt,
        task_id: uuid.UUID,
        db_session: AsyncSession,
    ):
        """Test that updating wrong type raises ValueError."""
        # Arrange - Create multiple choice answer first
        await repository.upsert_multiple_choice(
            sample_attempt.attempt_id,
            task_id,
            [uuid.uuid4()],
        )
        await db_session.commit()

        # Act & Assert
        with pytest.raises(AnswerTypeMismatchException):
            await repository.upsert_free_text(
                sample_attempt.attempt_id,
                task_id,
                "text",
            )

    # ==================== Cloze Tests ====================

    async def test_upsert_cloze_create(
        self,
        repository: AnswerRepository,
        sample_attempt: Attempt,
        task_id: uuid.UUID,
        db_session: AsyncSession,
    ):
        """Test creating a cloze answer."""
        # Arrange
        blank1, blank2 = uuid.uuid4(), uuid.uuid4()
        provided = [
            {"blank_id": blank1, "value": "answer1"},
            {"blank_id": blank2, "value": "answer2"},
        ]

        # Act
        answer = await repository.upsert_cloze(
            sample_attempt.attempt_id,
            task_id,
            provided,
        )
        await db_session.commit()

        # Assert
        assert isinstance(answer, ClozeAnswer)
        assert len(answer.items) == 2
        assert answer.task_id == task_id
        assert answer.attempt_id == sample_attempt.attempt_id

        # Verify items
        items_by_blank = {item.blank_id: item for item in answer.items}
        assert items_by_blank[blank1].provided_value == "answer1"
        assert items_by_blank[blank2].provided_value == "answer2"

    async def test_upsert_cloze_update_existing_items(
        self,
        repository: AnswerRepository,
        sample_attempt: Attempt,
        task_id: uuid.UUID,
        db_session: AsyncSession,
    ):
        """Test updating existing cloze items."""
        # Arrange
        blank1, blank2 = uuid.uuid4(), uuid.uuid4()

        # Create initial cloze answer
        await repository.upsert_cloze(
            sample_attempt.attempt_id,
            task_id,
            [
                {"blank_id": blank1, "value": "old1"},
                {"blank_id": blank2, "value": "old2"},
            ],
        )
        await db_session.commit()

        # Act - Update values
        answer = await repository.upsert_cloze(
            sample_attempt.attempt_id,
            task_id,
            [
                {"blank_id": blank1, "value": "new1"},
                {"blank_id": blank2, "value": "new2"},
            ],
        )
        await db_session.commit()

        # Assert
        items_by_blank = {item.blank_id: item for item in answer.items}
        assert items_by_blank[blank1].provided_value == "new1"
        assert items_by_blank[blank2].provided_value == "new2"

    async def test_upsert_cloze_partial_update(
        self,
        repository: AnswerRepository,
        sample_attempt: Attempt,
        task_id: uuid.UUID,
        db_session: AsyncSession,
    ):
        """Test updating only some cloze items."""
        # Arrange
        blank1, blank2, blank3 = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()

        # Create initial answer with 3 blanks
        await repository.upsert_cloze(
            sample_attempt.attempt_id,
            task_id,
            [
                {"blank_id": blank1, "value": "value1"},
                {"blank_id": blank2, "value": "value2"},
            ],
        )
        await db_session.commit()

        # Act - Update blank1 and add blank3
        answer = await repository.upsert_cloze(
            sample_attempt.attempt_id,
            task_id,
            [
                {"blank_id": blank1, "value": "updated1"},
                {"blank_id": blank3, "value": "value3"},
            ],
        )
        await db_session.commit()

        # Assert - All three blanks should exist
        assert len(answer.items) == 3
        items_by_blank = {item.blank_id: item for item in answer.items}
        assert items_by_blank[blank1].provided_value == "updated1"
        assert items_by_blank[blank2].provided_value == "value2"  # Unchanged
        assert items_by_blank[blank3].provided_value == "value3"  # New

    async def test_upsert_cloze_empty_list(
        self,
        repository: AnswerRepository,
        sample_attempt: Attempt,
        task_id: uuid.UUID,
        db_session: AsyncSession,
    ):
        """Test creating cloze answer with empty list."""
        # Act
        answer = await repository.upsert_cloze(
            sample_attempt.attempt_id,
            task_id,
            [],
        )
        await db_session.commit()

        # Assert
        assert isinstance(answer, ClozeAnswer)
        assert len(answer.items) == 0

    async def test_upsert_cloze_type_mismatch(
        self,
        repository: AnswerRepository,
        sample_attempt: Attempt,
        task_id: uuid.UUID,
        db_session: AsyncSession,
    ):
        """Test that updating wrong type raises ValueError."""
        # Arrange - Create free text answer first
        await repository.upsert_free_text(
            sample_attempt.attempt_id,
            task_id,
            "text",
        )
        await db_session.commit()

        # Act & Assert
        with pytest.raises(AnswerTypeMismatchException):
            await repository.upsert_cloze(
                sample_attempt.attempt_id,
                task_id,
                [],
            )

    # ==================== Get Tests ====================

    async def test_get_by_attempt_task(
        self,
        repository: AnswerRepository,
        sample_attempt: Attempt,
        task_id: uuid.UUID,
        db_session: AsyncSession,
    ):
        """Test getting answer by attempt and task."""
        # Arrange
        await repository.upsert_free_text(
            sample_attempt.attempt_id,
            task_id,
            "Test",
        )
        await db_session.commit()

        # Act
        found = await repository.get_by_attempt_task(
            sample_attempt.attempt_id,
            task_id,
        )

        # Assert
        assert found is not None
        assert isinstance(found, FreeTextAnswer)
        assert found.task_id == task_id

    async def test_get_by_attempt_task_not_found(
        self,
        repository: AnswerRepository,
        sample_attempt: Attempt,
    ):
        """Test getting non-existent answer returns None."""
        # Act
        found = await repository.get_by_attempt_task(
            sample_attempt.attempt_id,
            uuid.uuid4(),
        )

        # Assert
        assert found is None

    async def test_get_by_attempt_task_returns_correct_subtype(
        self,
        repository: AnswerRepository,
        sample_attempt: Attempt,
        db_session: AsyncSession,
    ):
        """Test that get returns correct polymorphic subtype."""
        # Arrange - Create one of each type
        task1, task2, task3 = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()

        await repository.upsert_multiple_choice(
            sample_attempt.attempt_id,
            task1,
            [uuid.uuid4()],
        )
        await repository.upsert_free_text(
            sample_attempt.attempt_id,
            task2,
            "text",
        )
        await repository.upsert_cloze(
            sample_attempt.attempt_id,
            task3,
            [{"blank_id": uuid.uuid4(), "value": "x"}],
        )
        await db_session.commit()

        # Act
        mc_answer = await repository.get_by_attempt_task(
            sample_attempt.attempt_id,
            task1,
        )
        ft_answer = await repository.get_by_attempt_task(
            sample_attempt.attempt_id,
            task2,
        )
        cloze_answer = await repository.get_by_attempt_task(
            sample_attempt.attempt_id,
            task3,
        )

        # Assert - Correct subtypes returned
        assert isinstance(mc_answer, MultipleChoiceAnswer)
        assert isinstance(ft_answer, FreeTextAnswer)
        assert isinstance(cloze_answer, ClozeAnswer)

    async def test_list_by_attempt(
        self,
        repository: AnswerRepository,
        sample_attempt: Attempt,
        db_session: AsyncSession,
    ):
        """Test listing all answers for an attempt."""
        # Arrange
        task1, task2, task3 = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()

        await repository.upsert_free_text(
            sample_attempt.attempt_id,
            task1,
            "Answer 1",
        )
        await repository.upsert_multiple_choice(
            sample_attempt.attempt_id,
            task2,
            [uuid.uuid4()],
        )
        await repository.upsert_cloze(
            sample_attempt.attempt_id,
            task3,
            [{"blank_id": uuid.uuid4(), "value": "x"}],
        )
        await db_session.commit()

        # Act
        answers = await repository.list_by_attempt(sample_attempt.attempt_id)

        # Assert
        assert len(answers) == 3

        # Verify all are correct subtypes
        types_found = {type(a) for a in answers}
        assert MultipleChoiceAnswer in types_found
        assert FreeTextAnswer in types_found
        assert ClozeAnswer in types_found

    async def test_list_by_attempt_empty(
        self,
        repository: AnswerRepository,
        sample_attempt: Attempt,
    ):
        """Test listing answers for attempt with no answers."""
        # Act
        answers = await repository.list_by_attempt(sample_attempt.attempt_id)

        # Assert
        assert answers == []

    async def test_list_by_attempt_eager_loads_nested_entities(
        self,
        repository: AnswerRepository,
        sample_attempt: Attempt,
        db_session: AsyncSession,
    ):
        """Test that list_by_attempt eagerly loads selections and items."""
        # Arrange
        task1, task2 = uuid.uuid4(), uuid.uuid4()
        opt1, opt2 = uuid.uuid4(), uuid.uuid4()
        blank1 = uuid.uuid4()

        await repository.upsert_multiple_choice(
            sample_attempt.attempt_id,
            task1,
            [opt1, opt2],
        )
        await repository.upsert_cloze(
            sample_attempt.attempt_id,
            task2,
            [{"blank_id": blank1, "value": "answer"}],
        )
        await db_session.commit()

        # Act
        answers = await repository.list_by_attempt(sample_attempt.attempt_id)

        # Assert - Nested entities are loaded
        mc_answer = next(a for a in answers if isinstance(a, MultipleChoiceAnswer))
        cloze_answer = next(a for a in answers if isinstance(a, ClozeAnswer))

        assert len(mc_answer.selections) == 2
        assert len(cloze_answer.items) == 1

    # ==================== Evaluation Tests ====================

    async def test_set_free_text_correctness_correct(
        self,
        repository: AnswerRepository,
        sample_attempt: Attempt,
        task_id: uuid.UUID,
        db_session: AsyncSession,
    ):
        """Test setting free text correctness to correct."""
        # Arrange
        await repository.upsert_free_text(
            sample_attempt.attempt_id,
            task_id,
            "Test",
        )
        await db_session.commit()

        # Act
        await repository.set_free_text_correctness(
            sample_attempt.attempt_id,
            task_id,
            True,
        )
        await db_session.commit()

        # Assert
        answer = await repository.get_by_attempt_task(
            sample_attempt.attempt_id,
            task_id,
        )
        assert answer.percentage_correct == Decimal("100.0")

    async def test_set_free_text_correctness_incorrect(
        self,
        repository: AnswerRepository,
        sample_attempt: Attempt,
        task_id: uuid.UUID,
        db_session: AsyncSession,
    ):
        """Test setting free text correctness to incorrect."""
        # Arrange
        await repository.upsert_free_text(
            sample_attempt.attempt_id,
            task_id,
            "Test",
        )
        await db_session.commit()

        # Act
        await repository.set_free_text_correctness(
            sample_attempt.attempt_id,
            task_id,
            False,
        )
        await db_session.commit()

        # Assert
        answer = await repository.get_by_attempt_task(
            sample_attempt.attempt_id,
            task_id,
        )
        assert answer.percentage_correct == Decimal("0.0")

    async def test_set_answer_percentage(
        self,
        repository: AnswerRepository,
        sample_attempt: Attempt,
        task_id: uuid.UUID,
        db_session: AsyncSession,
    ):
        """Test setting answer percentage."""
        # Arrange
        answer = await repository.upsert_free_text(
            sample_attempt.attempt_id,
            task_id,
            "Test",
        )
        await db_session.commit()

        # Act
        await repository.set_answer_percentage(answer.answer_id, Decimal("75.5"))
        await db_session.commit()

        # Assert
        found = await repository.get_by_attempt_task(
            sample_attempt.attempt_id,
            task_id,
        )
        assert found.percentage_correct == Decimal("75.5")

    async def test_set_cloze_item_correct(
        self,
        repository: AnswerRepository,
        sample_attempt: Attempt,
        task_id: uuid.UUID,
        db_session: AsyncSession,
    ):
        """Test setting cloze item correctness."""
        # Arrange
        blank1, blank2 = uuid.uuid4(), uuid.uuid4()
        answer = await repository.upsert_cloze(
            sample_attempt.attempt_id,
            task_id,
            [
                {"blank_id": blank1, "value": "correct"},
                {"blank_id": blank2, "value": "wrong"},
            ],
        )
        await db_session.commit()

        # Act
        await repository.set_cloze_item_correct(answer.answer_id, blank1, True)
        await repository.set_cloze_item_correct(answer.answer_id, blank2, False)
        await db_session.commit()

        # Assert
        found = await repository.get_by_attempt_task(
            sample_attempt.attempt_id,
            task_id,
        )
        items_by_blank = {item.blank_id: item for item in found.items}
        assert items_by_blank[blank1].is_correct is True
        assert items_by_blank[blank2].is_correct is False
