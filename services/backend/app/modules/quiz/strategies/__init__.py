"""Strategies for quiz module task handling."""

from app.shared.strategy_registry import StrategyRegistry
from app.modules.quiz.strategies.task_mapping_strategy import (
    TaskMappingStrategy,
    TaskTypeKey,
    normalize_task_type,
    MultipleChoiceTaskMappingStrategy,
    FreeTextTaskMappingStrategy,
    ClozeTaskMappingStrategy,
)
from app.modules.quiz.strategies.task_update_strategy import (
    TaskUpdateStrategy,
    MultipleChoiceTaskUpdateStrategy,
    FreeTextTaskUpdateStrategy,
    ClozeTaskUpdateStrategy,
)
from app.modules.quiz.strategies.task_clone_strategy import (
    TaskCloneStrategy,
    MultipleChoiceTaskCloneStrategy,
    FreeTextTaskCloneStrategy,
    ClozeTaskCloneStrategy,
)

TaskMappingRegistry = StrategyRegistry[TaskTypeKey, TaskMappingStrategy]
TaskUpdateRegistry = StrategyRegistry[TaskTypeKey, TaskUpdateStrategy]
TaskCloneRegistry = StrategyRegistry[TaskTypeKey, TaskCloneStrategy]


def task_mapping_registry() -> TaskMappingRegistry:
    return StrategyRegistry.from_strategies(
        strategies=[
            MultipleChoiceTaskMappingStrategy(),
            FreeTextTaskMappingStrategy(),
            ClozeTaskMappingStrategy(),
        ],
        key_getter=lambda strategy: strategy.task_type,
    )


def task_update_registry() -> TaskUpdateRegistry:
    return StrategyRegistry.from_strategies(
        strategies=[
            MultipleChoiceTaskUpdateStrategy(),
            FreeTextTaskUpdateStrategy(),
            ClozeTaskUpdateStrategy(),
        ],
        key_getter=lambda strategy: strategy.task_type,
    )


def task_clone_registry() -> TaskCloneRegistry:
    return StrategyRegistry.from_strategies(
        strategies=[
            MultipleChoiceTaskCloneStrategy(),
            FreeTextTaskCloneStrategy(),
            ClozeTaskCloneStrategy(),
        ],
        key_getter=lambda strategy: strategy.task_type,
    )


__all__ = [
    "TaskMappingRegistry",
    "TaskMappingStrategy",
    "TaskTypeKey",
    "TaskUpdateRegistry",
    "TaskUpdateStrategy",
    "TaskCloneRegistry",
    "TaskCloneStrategy",
    "normalize_task_type",
    "task_mapping_registry",
    "task_update_registry",
    "task_clone_registry",
]
