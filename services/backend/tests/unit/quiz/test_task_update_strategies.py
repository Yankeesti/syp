"""Tests for task update strategies."""

import uuid

import pytest

from app.modules.quiz.models.task import (
    TaskType,
    MultipleChoiceTask,
    TaskMultipleChoiceOption,
    FreeTextTask,
    ClozeTask,
    TaskClozeBlank,
)
from app.modules.quiz.schemas.task_input import (
    MultipleChoiceTaskUpdate,
    MultipleChoiceOptionUpdate,
    FreeTextTaskUpdate,
    ClozeTaskUpdate,
    ClozeBlankUpdate,
)
from app.modules.quiz.strategies.task_update_strategy import (
    MultipleChoiceTaskUpdateStrategy,
    FreeTextTaskUpdateStrategy,
    ClozeTaskUpdateStrategy,
)


class TestMultipleChoiceTaskUpdateStrategy:
    """Tests for MultipleChoiceTaskUpdateStrategy."""

    def _create_mc_task(self) -> MultipleChoiceTask:
        """Create a test MultipleChoiceTask with options."""
        task = MultipleChoiceTask(
            task_id=uuid.uuid4(),
            quiz_id=uuid.uuid4(),
            type=TaskType.MULTIPLE_CHOICE,
            prompt="Original prompt?",
            topic_detail="Original topic",
            order_index=0,
        )
        task.options = [
            TaskMultipleChoiceOption(
                option_id=uuid.uuid4(),
                text="Option A",
                is_correct=True,
                explanation="A is correct",
            ),
            TaskMultipleChoiceOption(
                option_id=uuid.uuid4(),
                text="Option B",
                is_correct=False,
                explanation=None,
            ),
        ]
        return task

    def test_update_prompt_only(self) -> None:
        """Test updating only the prompt field."""
        task = self._create_mc_task()
        original_topic = task.topic_detail
        original_options_count = len(task.options)

        update_dto = MultipleChoiceTaskUpdate(
            type="multiple_choice",
            prompt="New prompt?",
        )

        strategy = MultipleChoiceTaskUpdateStrategy()
        updated = strategy.apply_update(task, update_dto)

        assert updated.prompt == "New prompt?"
        assert updated.topic_detail == original_topic
        assert len(updated.options) == original_options_count

    def test_update_topic_detail_only(self) -> None:
        """Test updating only the topic_detail field."""
        task = self._create_mc_task()
        original_prompt = task.prompt

        update_dto = MultipleChoiceTaskUpdate(
            type="multiple_choice",
            topic_detail="New topic",
        )

        strategy = MultipleChoiceTaskUpdateStrategy()
        updated = strategy.apply_update(task, update_dto)

        assert updated.prompt == original_prompt
        assert updated.topic_detail == "New topic"

    def test_update_options_replace_all(self) -> None:
        """Test that options are completely replaced (Replace-All semantics)."""
        task = self._create_mc_task()
        original_option_ids = [opt.option_id for opt in task.options]

        update_dto = MultipleChoiceTaskUpdate(
            type="multiple_choice",
            options=[
                MultipleChoiceOptionUpdate(
                    text="New Option 1",
                    is_correct=False,
                    explanation="Explanation 1",
                ),
                MultipleChoiceOptionUpdate(
                    text="New Option 2",
                    is_correct=True,
                    explanation="Explanation 2",
                ),
                MultipleChoiceOptionUpdate(
                    text="New Option 3",
                    is_correct=False,
                    explanation=None,
                ),
            ],
        )

        strategy = MultipleChoiceTaskUpdateStrategy()
        updated = strategy.apply_update(task, update_dto)

        # Should have 3 new options
        assert len(updated.options) == 3

        # New options should have new IDs (not the original ones)
        new_option_ids = [opt.option_id for opt in updated.options]
        for old_id in original_option_ids:
            assert old_id not in new_option_ids

        # Verify content
        assert updated.options[0].text == "New Option 1"
        assert updated.options[0].is_correct is False
        assert updated.options[1].text == "New Option 2"
        assert updated.options[1].is_correct is True
        assert updated.options[2].text == "New Option 3"
        assert updated.options[2].explanation is None

    def test_update_all_fields(self) -> None:
        """Test updating all fields at once."""
        task = self._create_mc_task()

        update_dto = MultipleChoiceTaskUpdate(
            type="multiple_choice",
            prompt="Completely new prompt?",
            topic_detail="Completely new topic",
            options=[
                MultipleChoiceOptionUpdate(
                    text="Single new option",
                    is_correct=True,
                    explanation="The only option",
                ),
            ],
        )

        strategy = MultipleChoiceTaskUpdateStrategy()
        updated = strategy.apply_update(task, update_dto)

        assert updated.prompt == "Completely new prompt?"
        assert updated.topic_detail == "Completely new topic"
        assert len(updated.options) == 1
        assert updated.options[0].text == "Single new option"

    def test_partial_update_preserves_options(self) -> None:
        """Test that options are preserved when not included in update."""
        task = self._create_mc_task()
        original_options = [(opt.text, opt.is_correct) for opt in task.options]

        update_dto = MultipleChoiceTaskUpdate(
            type="multiple_choice",
            prompt="Updated prompt only",
            # options is None - should preserve existing
        )

        strategy = MultipleChoiceTaskUpdateStrategy()
        updated = strategy.apply_update(task, update_dto)

        assert updated.prompt == "Updated prompt only"
        current_options = [(opt.text, opt.is_correct) for opt in updated.options]
        assert current_options == original_options

    def test_rejects_wrong_task_type(self) -> None:
        """Test that strategy rejects non-MultipleChoiceTask."""
        task = FreeTextTask(
            task_id=uuid.uuid4(),
            quiz_id=uuid.uuid4(),
            type=TaskType.FREE_TEXT,
            prompt="Wrong type",
            topic_detail="Topic",
            order_index=0,
            reference_answer="Answer",
        )

        update_dto = MultipleChoiceTaskUpdate(
            type="multiple_choice",
            prompt="New prompt",
        )

        strategy = MultipleChoiceTaskUpdateStrategy()
        with pytest.raises(ValueError, match="Expected MultipleChoiceTask"):
            strategy.apply_update(task, update_dto)

    def test_rejects_wrong_dto_type(self) -> None:
        """Test that strategy rejects non-MultipleChoiceTaskUpdate DTO."""
        task = self._create_mc_task()

        update_dto = FreeTextTaskUpdate(
            type="free_text",
            prompt="Wrong DTO",
        )

        strategy = MultipleChoiceTaskUpdateStrategy()
        with pytest.raises(ValueError, match="Expected MultipleChoiceTaskUpdate"):
            strategy.apply_update(task, update_dto)


class TestFreeTextTaskUpdateStrategy:
    """Tests for FreeTextTaskUpdateStrategy."""

    def _create_free_text_task(self) -> FreeTextTask:
        """Create a test FreeTextTask."""
        return FreeTextTask(
            task_id=uuid.uuid4(),
            quiz_id=uuid.uuid4(),
            type=TaskType.FREE_TEXT,
            prompt="Original question?",
            topic_detail="Original topic",
            order_index=0,
            reference_answer="Original reference answer",
        )

    def test_update_prompt_only(self) -> None:
        """Test updating only the prompt field."""
        task = self._create_free_text_task()
        original_reference = task.reference_answer

        update_dto = FreeTextTaskUpdate(
            type="free_text",
            prompt="New question?",
        )

        strategy = FreeTextTaskUpdateStrategy()
        updated = strategy.apply_update(task, update_dto)

        assert updated.prompt == "New question?"
        assert updated.reference_answer == original_reference

    def test_update_reference_answer_only(self) -> None:
        """Test updating only the reference_answer field."""
        task = self._create_free_text_task()
        original_prompt = task.prompt

        update_dto = FreeTextTaskUpdate(
            type="free_text",
            reference_answer="New reference answer",
        )

        strategy = FreeTextTaskUpdateStrategy()
        updated = strategy.apply_update(task, update_dto)

        assert updated.prompt == original_prompt
        assert updated.reference_answer == "New reference answer"

    def test_update_all_fields(self) -> None:
        """Test updating all fields at once."""
        task = self._create_free_text_task()

        update_dto = FreeTextTaskUpdate(
            type="free_text",
            prompt="New prompt?",
            topic_detail="New topic",
            reference_answer="New answer",
        )

        strategy = FreeTextTaskUpdateStrategy()
        updated = strategy.apply_update(task, update_dto)

        assert updated.prompt == "New prompt?"
        assert updated.topic_detail == "New topic"
        assert updated.reference_answer == "New answer"

    def test_partial_update_preserves_fields(self) -> None:
        """Test that fields not in update are preserved."""
        task = self._create_free_text_task()
        original_prompt = task.prompt
        original_topic = task.topic_detail
        original_answer = task.reference_answer

        # Update with all None (only type is set)
        update_dto = FreeTextTaskUpdate(type="free_text")

        strategy = FreeTextTaskUpdateStrategy()
        updated = strategy.apply_update(task, update_dto)

        assert updated.prompt == original_prompt
        assert updated.topic_detail == original_topic
        assert updated.reference_answer == original_answer

    def test_rejects_wrong_task_type(self) -> None:
        """Test that strategy rejects non-FreeTextTask."""
        task = MultipleChoiceTask(
            task_id=uuid.uuid4(),
            quiz_id=uuid.uuid4(),
            type=TaskType.MULTIPLE_CHOICE,
            prompt="Wrong type",
            topic_detail="Topic",
            order_index=0,
        )
        task.options = []

        update_dto = FreeTextTaskUpdate(
            type="free_text",
            prompt="New prompt",
        )

        strategy = FreeTextTaskUpdateStrategy()
        with pytest.raises(ValueError, match="Expected FreeTextTask"):
            strategy.apply_update(task, update_dto)

    def test_rejects_wrong_dto_type(self) -> None:
        """Test that strategy rejects non-FreeTextTaskUpdate DTO."""
        task = self._create_free_text_task()

        update_dto = ClozeTaskUpdate(
            type="cloze",
            prompt="Wrong DTO",
        )

        strategy = FreeTextTaskUpdateStrategy()
        with pytest.raises(ValueError, match="Expected FreeTextTaskUpdate"):
            strategy.apply_update(task, update_dto)


class TestClozeTaskUpdateStrategy:
    """Tests for ClozeTaskUpdateStrategy."""

    def _create_cloze_task(self) -> ClozeTask:
        """Create a test ClozeTask with blanks."""
        task = ClozeTask(
            task_id=uuid.uuid4(),
            quiz_id=uuid.uuid4(),
            type=TaskType.CLOZE,
            prompt="Fill in the blanks",
            topic_detail="Original topic",
            order_index=0,
            template_text="The {{blank_0}} is {{blank_1}}.",
        )
        task.blanks = [
            TaskClozeBlank(
                blank_id=uuid.uuid4(),
                position=0,
                expected_value="answer",
            ),
            TaskClozeBlank(
                blank_id=uuid.uuid4(),
                position=1,
                expected_value="correct",
            ),
        ]
        return task

    def test_update_prompt_only(self) -> None:
        """Test updating only the prompt field."""
        task = self._create_cloze_task()
        original_template = task.template_text
        original_blanks_count = len(task.blanks)

        update_dto = ClozeTaskUpdate(
            type="cloze",
            prompt="New instruction",
        )

        strategy = ClozeTaskUpdateStrategy()
        updated = strategy.apply_update(task, update_dto)

        assert updated.prompt == "New instruction"
        assert updated.template_text == original_template
        assert len(updated.blanks) == original_blanks_count

    def test_update_template_text_only(self) -> None:
        """Test updating only the template_text field."""
        task = self._create_cloze_task()
        original_prompt = task.prompt

        update_dto = ClozeTaskUpdate(
            type="cloze",
            template_text="New {{blank_0}} template.",
        )

        strategy = ClozeTaskUpdateStrategy()
        updated = strategy.apply_update(task, update_dto)

        assert updated.prompt == original_prompt
        assert updated.template_text == "New {{blank_0}} template."

    def test_update_blanks_replace_all(self) -> None:
        """Test that blanks are completely replaced (Replace-All semantics)."""
        task = self._create_cloze_task()
        original_blank_ids = [blank.blank_id for blank in task.blanks]

        update_dto = ClozeTaskUpdate(
            type="cloze",
            blanks=[
                ClozeBlankUpdate(position=0, expected_value="new_value_0"),
                ClozeBlankUpdate(position=1, expected_value="new_value_1"),
                ClozeBlankUpdate(position=2, expected_value="new_value_2"),
            ],
        )

        strategy = ClozeTaskUpdateStrategy()
        updated = strategy.apply_update(task, update_dto)

        # Should have 3 new blanks
        assert len(updated.blanks) == 3

        # New blanks should have new IDs
        new_blank_ids = [blank.blank_id for blank in updated.blanks]
        for old_id in original_blank_ids:
            assert old_id not in new_blank_ids

        # Verify content
        assert updated.blanks[0].position == 0
        assert updated.blanks[0].expected_value == "new_value_0"
        assert updated.blanks[1].position == 1
        assert updated.blanks[1].expected_value == "new_value_1"
        assert updated.blanks[2].position == 2
        assert updated.blanks[2].expected_value == "new_value_2"

    def test_update_template_and_blanks_together(self) -> None:
        """Test updating template_text and blanks together."""
        task = self._create_cloze_task()

        update_dto = ClozeTaskUpdate(
            type="cloze",
            template_text="Completely {{blank_0}} new {{blank_1}} template {{blank_2}}.",
            blanks=[
                ClozeBlankUpdate(position=0, expected_value="first"),
                ClozeBlankUpdate(position=1, expected_value="second"),
                ClozeBlankUpdate(position=2, expected_value="third"),
            ],
        )

        strategy = ClozeTaskUpdateStrategy()
        updated = strategy.apply_update(task, update_dto)

        assert "Completely" in updated.template_text
        assert len(updated.blanks) == 3

    def test_update_all_fields(self) -> None:
        """Test updating all fields at once."""
        task = self._create_cloze_task()

        update_dto = ClozeTaskUpdate(
            type="cloze",
            prompt="New prompt",
            topic_detail="New topic",
            template_text="Single {{blank_0}}.",
            blanks=[
                ClozeBlankUpdate(position=0, expected_value="blank"),
            ],
        )

        strategy = ClozeTaskUpdateStrategy()
        updated = strategy.apply_update(task, update_dto)

        assert updated.prompt == "New prompt"
        assert updated.topic_detail == "New topic"
        assert updated.template_text == "Single {{blank_0}}."
        assert len(updated.blanks) == 1

    def test_partial_update_preserves_blanks(self) -> None:
        """Test that blanks are preserved when not included in update."""
        task = self._create_cloze_task()
        original_blanks = [
            (blank.position, blank.expected_value) for blank in task.blanks
        ]

        update_dto = ClozeTaskUpdate(
            type="cloze",
            prompt="Updated prompt only",
            # blanks is None - should preserve existing
        )

        strategy = ClozeTaskUpdateStrategy()
        updated = strategy.apply_update(task, update_dto)

        assert updated.prompt == "Updated prompt only"
        current_blanks = [
            (blank.position, blank.expected_value) for blank in updated.blanks
        ]
        assert current_blanks == original_blanks

    def test_remove_all_blanks(self) -> None:
        """Test replacing blanks with empty list."""
        task = self._create_cloze_task()
        assert len(task.blanks) > 0

        update_dto = ClozeTaskUpdate(
            type="cloze",
            template_text="No blanks in this text.",
            blanks=[],  # Empty list removes all blanks
        )

        strategy = ClozeTaskUpdateStrategy()
        updated = strategy.apply_update(task, update_dto)

        assert len(updated.blanks) == 0

    def test_rejects_wrong_task_type(self) -> None:
        """Test that strategy rejects non-ClozeTask."""
        task = FreeTextTask(
            task_id=uuid.uuid4(),
            quiz_id=uuid.uuid4(),
            type=TaskType.FREE_TEXT,
            prompt="Wrong type",
            topic_detail="Topic",
            order_index=0,
            reference_answer="Answer",
        )

        update_dto = ClozeTaskUpdate(
            type="cloze",
            prompt="New prompt",
        )

        strategy = ClozeTaskUpdateStrategy()
        with pytest.raises(ValueError, match="Expected ClozeTask"):
            strategy.apply_update(task, update_dto)

    def test_rejects_wrong_dto_type(self) -> None:
        """Test that strategy rejects non-ClozeTaskUpdate DTO."""
        task = self._create_cloze_task()

        update_dto = MultipleChoiceTaskUpdate(
            type="multiple_choice",
            prompt="Wrong DTO",
        )

        strategy = ClozeTaskUpdateStrategy()
        with pytest.raises(ValueError, match="Expected ClozeTaskUpdate"):
            strategy.apply_update(task, update_dto)


class TestTaskUpdateRegistry:
    """Tests for the task update registry."""

    def test_registry_contains_all_strategies(self) -> None:
        """Test that registry has all task type strategies."""
        from app.modules.quiz.strategies import task_update_registry

        registry = task_update_registry()

        # Should be able to get strategy for each type
        mc_strategy = registry.get("multiple_choice")
        assert isinstance(mc_strategy, MultipleChoiceTaskUpdateStrategy)

        ft_strategy = registry.get("free_text")
        assert isinstance(ft_strategy, FreeTextTaskUpdateStrategy)

        cloze_strategy = registry.get("cloze")
        assert isinstance(cloze_strategy, ClozeTaskUpdateStrategy)

    def test_registry_raises_for_unknown_type(self) -> None:
        """Test that registry raises error for unknown task type."""
        from app.modules.quiz.strategies import task_update_registry
        from app.shared.strategy_registry import StrategyNotFoundError

        registry = task_update_registry()

        with pytest.raises(StrategyNotFoundError):
            registry.get("unknown_type")
