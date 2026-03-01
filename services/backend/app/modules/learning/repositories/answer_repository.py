"""Answer repository (polymorphic data access).

Encapsulates DB operations for all answer types and keeps services slim.
"""

from uuid import UUID
from decimal import Decimal

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import with_polymorphic, selectinload

from app.modules.learning.models import (
    Answer,
    AnswerType,
    MultipleChoiceAnswer,
    AnswerMultipleChoiceSelection,
    FreeTextAnswer,
    ClozeAnswer,
    AnswerClozeItem,
)
from app.modules.learning.exceptions import (
    AnswerTypeMismatchException,
    InvalidAnswerTypeException,
)


class AnswerRepository:
    """Repository for Answer database operations (all types)."""

    def __init__(self, db: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            db: Async SQLAlchemy session
        """
        self.db = db

    def _get_polymorphic_entity(self):
        """Get polymorphic entity for Answer queries with all subtypes."""
        return with_polymorphic(
            Answer,
            [MultipleChoiceAnswer, FreeTextAnswer, ClozeAnswer],
        )

    async def _load_answer_relationships(self, answer: Answer) -> None:
        """
        Load nested relationships for an answer based on its type.

        Args:
            answer: Answer instance (may be MultipleChoiceAnswer or ClozeAnswer)
        """
        if isinstance(answer, MultipleChoiceAnswer):
            await self.db.refresh(answer, ["selections"])
        elif isinstance(answer, ClozeAnswer):
            await self.db.refresh(answer, ["items"])

    async def get_by_attempt_task(
        self,
        attempt_id: UUID,
        task_id: UUID,
    ) -> Answer | None:
        """
        Get answer for specific attempt and task with all subtype data loaded.

        SQLAlchemy automatically returns the correct subclass
        (MultipleChoiceAnswer/FreeTextAnswer/ClozeAnswer) based on polymorphic identity.

        Eagerly loads nested entities:
        - MultipleChoiceAnswer.selections
        - ClozeAnswer.items

        Args:
            attempt_id: UUID of the attempt
            task_id: UUID of the task

        Returns:
            Answer subclass instance if found, None otherwise
        """
        # Use with_polymorphic to eagerly load all subclass columns
        # This is required for async SQLAlchemy to avoid lazy loading issues
        poly = self._get_polymorphic_entity()
        stmt = select(poly).where(
            poly.attempt_id == attempt_id,
            poly.task_id == task_id,
        )
        result = await self.db.execute(stmt)
        answer = result.scalar_one_or_none()

        if answer:
            # Explicitly load nested relationships based on answer type
            # This ensures compatibility with async SQLite (aiosqlite)
            await self._load_answer_relationships(answer)

        return answer

    async def list_by_attempt(self, attempt_id: UUID) -> list[Answer]:
        """
        List all answers for an attempt with all subtype data loaded.

        Eagerly loads nested entities for all answer types.

        Args:
            attempt_id: UUID of the attempt

        Returns:
            List of Answer subclass instances
        """
        # Use with_polymorphic to eagerly load all subclass columns
        poly = self._get_polymorphic_entity()
        stmt = select(poly).where(poly.attempt_id == attempt_id)
        result = await self.db.execute(stmt)
        answers = list(result.scalars().all())

        # Explicitly load nested relationships for each answer
        for answer in answers:
            await self._load_answer_relationships(answer)

        return answers

    async def upsert_multiple_choice(
        self,
        attempt_id: UUID,
        task_id: UUID,
        selected_option_ids: list[UUID],
    ) -> MultipleChoiceAnswer:
        """
        Upsert multiple choice answer with idempotent selection handling.

        Performs a diff between current and new selections:
        - Removes deselected options
        - Adds newly selected options
        - Keeps unchanged selections

        This enables auto-save functionality where users can change their selections.

        Args:
            attempt_id: UUID of the attempt
            task_id: UUID of the task
            selected_option_ids: List of option UUIDs to be selected

        Returns:
            Updated MultipleChoiceAnswer instance with selections

        Raises:
            AnswerTypeMismatchException: If answer exists but is not multiple_choice
        """
        # Find or create base answer
        existing = await self._get_or_create_answer(
            attempt_id,
            task_id,
            AnswerType.MULTIPLE_CHOICE,
        )

        if not isinstance(existing, MultipleChoiceAnswer):
            raise AnswerTypeMismatchException(
                "multiple_choice",
                "free_text" if isinstance(existing, FreeTextAnswer) else "cloze",
            )

        # Get current selections
        await self.db.refresh(existing, ["selections"])
        current_option_ids = {s.option_id for s in existing.selections}
        new_option_ids = set(selected_option_ids)

        # Remove deselected options
        to_remove = current_option_ids - new_option_ids
        if to_remove:
            for selection in list(existing.selections):
                if selection.option_id in to_remove:
                    await self.db.delete(selection)

        # Add newly selected options
        to_add = new_option_ids - current_option_ids
        for option_id in to_add:
            selection = AnswerMultipleChoiceSelection(
                answer_id=existing.answer_id,
                option_id=option_id,
            )
            self.db.add(selection)

        await self.db.flush()
        await self.db.refresh(existing, ["selections"])
        return existing

    async def upsert_free_text(
        self,
        attempt_id: UUID,
        task_id: UUID,
        text_response: str,
    ) -> FreeTextAnswer:
        """
        Upsert free text answer.

        Updates text_response if answer exists, creates new one otherwise.
        Enables auto-save functionality.

        Args:
            attempt_id: UUID of the attempt
            task_id: UUID of the task
            text_response: User's text answer

        Returns:
            Updated FreeTextAnswer instance

        Raises:
            AnswerTypeMismatchException: If answer exists but is not free_text
        """
        existing = await self._get_or_create_answer(
            attempt_id,
            task_id,
            AnswerType.FREE_TEXT,
        )

        if not isinstance(existing, FreeTextAnswer):
            raise AnswerTypeMismatchException(
                "free_text",
                (
                    "multiple_choice"
                    if isinstance(existing, MultipleChoiceAnswer)
                    else "cloze"
                ),
            )

        existing.text_response = text_response
        await self.db.flush()
        return existing

    async def upsert_cloze(
        self,
        attempt_id: UUID,
        task_id: UUID,
        provided_values: list[dict],
    ) -> ClozeAnswer:
        """
        Upsert cloze answer with items.

        Performs upsert on each blank item:
        - Updates existing items
        - Creates new items

        Enables auto-save functionality where users can fill blanks incrementally.

        Args:
            attempt_id: UUID of the attempt
            task_id: UUID of the task
            provided_values: List of dicts with keys:
                - blank_id: UUID of the blank
                - value: User's provided text for this blank

        Returns:
            Updated ClozeAnswer instance with items

        Raises:
            AnswerTypeMismatchException: If answer exists but is not cloze

        Example:
            provided_values = [
                {"blank_id": uuid1, "value": "Paris"},
                {"blank_id": uuid2, "value": "France"},
            ]
        """
        existing = await self._get_or_create_answer(
            attempt_id,
            task_id,
            AnswerType.CLOZE,
        )

        if not isinstance(existing, ClozeAnswer):
            raise AnswerTypeMismatchException(
                "cloze",
                (
                    "multiple_choice"
                    if isinstance(existing, MultipleChoiceAnswer)
                    else "free_text"
                ),
            )

        # Load existing items
        await self.db.refresh(existing, ["items"])
        existing_items = {item.blank_id: item for item in existing.items}

        # Upsert each provided value
        for pv in provided_values:
            blank_id = pv["blank_id"]
            value = pv["value"]

            if blank_id in existing_items:
                # Update existing item
                existing_items[blank_id].provided_value = value
            else:
                # Create new item
                item = AnswerClozeItem(
                    answer_id=existing.answer_id,
                    blank_id=blank_id,
                    provided_value=value,
                )
                self.db.add(item)

        await self.db.flush()
        await self.db.refresh(existing, ["items"])
        return existing

    async def _get_or_create_answer(
        self,
        attempt_id: UUID,
        task_id: UUID,
        answer_type: AnswerType,
    ) -> Answer:
        """
        Get existing answer or create new one of specified type.

        Helper method for upsert operations.

        Args:
            attempt_id: UUID of the attempt
            task_id: UUID of the task
            answer_type: Type of answer to create if not exists

        Returns:
            Existing or newly created Answer instance

        Raises:
            InvalidAnswerTypeException: If unknown answer_type provided
        """
        # Check for existing answer
        poly = self._get_polymorphic_entity()
        stmt = select(poly).where(
            poly.attempt_id == attempt_id,
            poly.task_id == task_id,
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            return existing

        # Create new answer based on type
        if answer_type == AnswerType.MULTIPLE_CHOICE:
            answer = MultipleChoiceAnswer(
                attempt_id=attempt_id,
                task_id=task_id,
            )
        elif answer_type == AnswerType.FREE_TEXT:
            answer = FreeTextAnswer(
                attempt_id=attempt_id,
                task_id=task_id,
                text_response="",  # Will be updated immediately after
            )
        elif answer_type == AnswerType.CLOZE:
            answer = ClozeAnswer(
                attempt_id=attempt_id,
                task_id=task_id,
            )
        else:
            raise InvalidAnswerTypeException(str(answer_type), str(answer_type))

        self.db.add(answer)
        await self.db.flush()
        return answer

    async def set_free_text_correctness(
        self,
        attempt_id: UUID,
        task_id: UUID,
        is_correct: bool,
    ) -> None:
        """
        Set percentage_correct for free text answer (0.0 or 100.0).

        Used by evaluation service after LLM evaluation.

        Args:
            attempt_id: UUID of the attempt
            task_id: UUID of the task
            is_correct: Whether the answer is correct
        """
        answer = await self.get_by_attempt_task(attempt_id, task_id)
        if answer and isinstance(answer, FreeTextAnswer):
            answer.percentage_correct = (
                Decimal("100.0") if is_correct else Decimal("0.0")
            )
            await self.db.flush()

    async def set_answer_percentage(self, answer_id: UUID, percentage: Decimal) -> None:
        """
        Set percentage_correct on any answer.

        Generic method for setting evaluation result.

        Args:
            answer_id: UUID of the answer
            percentage: Percentage correct (0-100)
        """
        stmt = select(Answer).where(Answer.answer_id == answer_id)
        result = await self.db.execute(stmt)
        answer = result.scalar_one_or_none()
        if answer:
            answer.percentage_correct = percentage
            await self.db.flush()

    async def set_cloze_item_correct(
        self,
        answer_id: UUID,
        blank_id: UUID,
        is_correct: bool,
    ) -> None:
        """
        Set is_correct on a specific cloze item.

        Used by evaluation service to mark individual blanks as correct/incorrect.

        Args:
            answer_id: UUID of the answer
            blank_id: UUID of the blank
            is_correct: Whether the provided value is correct
        """
        stmt = select(AnswerClozeItem).where(
            AnswerClozeItem.answer_id == answer_id,
            AnswerClozeItem.blank_id == blank_id,
        )
        result = await self.db.execute(stmt)
        item = result.scalar_one_or_none()
        if item:
            item.is_correct = is_correct
            await self.db.flush()
