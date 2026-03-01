"""Tests for task clone strategies."""

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
from app.modules.quiz.strategies.task_clone_strategy import (
    MultipleChoiceTaskCloneStrategy,
    FreeTextTaskCloneStrategy,
    ClozeTaskCloneStrategy,
)


class TestMultipleChoiceTaskCloneStrategy:
    """Tests for MultipleChoiceTaskCloneStrategy."""

    def _create_task(self) -> MultipleChoiceTask:
        task = MultipleChoiceTask(
            task_id=uuid.uuid4(),
            quiz_id=uuid.uuid4(),
            quiz_version_id=uuid.uuid4(),
            type=TaskType.MULTIPLE_CHOICE,
            prompt="Original prompt?",
            topic_detail="Original topic",
            order_index=1,
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

    def test_clone_copies_fields_and_options(self) -> None:
        task = self._create_task()
        target_version_id = uuid.uuid4()

        strategy = MultipleChoiceTaskCloneStrategy()
        cloned = strategy.clone(task, target_version_id)

        assert isinstance(cloned, MultipleChoiceTask)
        assert cloned is not task
        assert cloned.quiz_id == task.quiz_id
        assert cloned.quiz_version_id == target_version_id
        assert cloned.prompt == task.prompt
        assert cloned.topic_detail == task.topic_detail
        assert cloned.order_index == task.order_index
        assert len(cloned.options) == len(task.options)

        for original, copied in zip(task.options, cloned.options, strict=True):
            assert copied is not original
            assert copied.text == original.text
            assert copied.is_correct == original.is_correct
            assert copied.explanation == original.explanation

    def test_rejects_wrong_task_type(self) -> None:
        task = FreeTextTask(
            task_id=uuid.uuid4(),
            quiz_id=uuid.uuid4(),
            quiz_version_id=uuid.uuid4(),
            type=TaskType.FREE_TEXT,
            prompt="Wrong type",
            topic_detail="Topic",
            order_index=0,
            reference_answer="Answer",
        )

        strategy = MultipleChoiceTaskCloneStrategy()
        with pytest.raises(ValueError, match="Expected MultipleChoiceTask"):
            strategy.clone(task, uuid.uuid4())


class TestFreeTextTaskCloneStrategy:
    """Tests for FreeTextTaskCloneStrategy."""

    def _create_task(self) -> FreeTextTask:
        return FreeTextTask(
            task_id=uuid.uuid4(),
            quiz_id=uuid.uuid4(),
            quiz_version_id=uuid.uuid4(),
            type=TaskType.FREE_TEXT,
            prompt="Original prompt?",
            topic_detail="Original topic",
            order_index=2,
            reference_answer="Original answer",
        )

    def test_clone_copies_fields(self) -> None:
        task = self._create_task()
        target_version_id = uuid.uuid4()

        strategy = FreeTextTaskCloneStrategy()
        cloned = strategy.clone(task, target_version_id)

        assert isinstance(cloned, FreeTextTask)
        assert cloned is not task
        assert cloned.quiz_id == task.quiz_id
        assert cloned.quiz_version_id == target_version_id
        assert cloned.prompt == task.prompt
        assert cloned.topic_detail == task.topic_detail
        assert cloned.order_index == task.order_index
        assert cloned.reference_answer == task.reference_answer

    def test_rejects_wrong_task_type(self) -> None:
        task = ClozeTask(
            task_id=uuid.uuid4(),
            quiz_id=uuid.uuid4(),
            quiz_version_id=uuid.uuid4(),
            type=TaskType.CLOZE,
            prompt="Wrong type",
            topic_detail="Topic",
            order_index=0,
            template_text="{{blank_1}}",
        )

        strategy = FreeTextTaskCloneStrategy()
        with pytest.raises(ValueError, match="Expected FreeTextTask"):
            strategy.clone(task, uuid.uuid4())


class TestClozeTaskCloneStrategy:
    """Tests for ClozeTaskCloneStrategy."""

    def _create_task(self) -> ClozeTask:
        task = ClozeTask(
            task_id=uuid.uuid4(),
            quiz_id=uuid.uuid4(),
            quiz_version_id=uuid.uuid4(),
            type=TaskType.CLOZE,
            prompt="Original prompt?",
            topic_detail="Original topic",
            order_index=3,
            template_text="{{blank_1}}",
        )
        task.blanks = [
            TaskClozeBlank(
                blank_id=uuid.uuid4(),
                position=1,
                expected_value="Answer",
            ),
        ]
        return task

    def test_clone_copies_fields_and_blanks(self) -> None:
        task = self._create_task()
        target_version_id = uuid.uuid4()

        strategy = ClozeTaskCloneStrategy()
        cloned = strategy.clone(task, target_version_id)

        assert isinstance(cloned, ClozeTask)
        assert cloned is not task
        assert cloned.quiz_id == task.quiz_id
        assert cloned.quiz_version_id == target_version_id
        assert cloned.prompt == task.prompt
        assert cloned.topic_detail == task.topic_detail
        assert cloned.order_index == task.order_index
        assert cloned.template_text == task.template_text
        assert len(cloned.blanks) == len(task.blanks)

        for original, copied in zip(task.blanks, cloned.blanks, strict=True):
            assert copied is not original
            assert copied.position == original.position
            assert copied.expected_value == original.expected_value

    def test_rejects_wrong_task_type(self) -> None:
        task = MultipleChoiceTask(
            task_id=uuid.uuid4(),
            quiz_id=uuid.uuid4(),
            quiz_version_id=uuid.uuid4(),
            type=TaskType.MULTIPLE_CHOICE,
            prompt="Wrong type",
            topic_detail="Topic",
            order_index=0,
        )

        strategy = ClozeTaskCloneStrategy()
        with pytest.raises(ValueError, match="Expected ClozeTask"):
            strategy.clone(task, uuid.uuid4())


class TestTaskCloneRegistry:
    """Tests for the task clone registry."""

    def test_registry_contains_all_strategies(self) -> None:
        from app.modules.quiz.strategies import task_clone_registry

        registry = task_clone_registry()

        mc_strategy = registry.get("multiple_choice")
        assert isinstance(mc_strategy, MultipleChoiceTaskCloneStrategy)

        ft_strategy = registry.get("free_text")
        assert isinstance(ft_strategy, FreeTextTaskCloneStrategy)

        cloze_strategy = registry.get("cloze")
        assert isinstance(cloze_strategy, ClozeTaskCloneStrategy)

    def test_registry_raises_for_unknown_type(self) -> None:
        from app.modules.quiz.strategies import task_clone_registry
        from app.shared.strategy_registry import StrategyNotFoundError

        registry = task_clone_registry()

        with pytest.raises(StrategyNotFoundError):
            registry.get("unknown_type")
