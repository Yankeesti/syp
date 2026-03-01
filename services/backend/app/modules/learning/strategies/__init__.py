"""Strategies for learning module answer handling."""

from app.shared.strategy_registry import StrategyRegistry
from app.modules.learning.strategies.answer_types import (
    AnswerTypeKey,
    normalize_answer_type,
)
from app.modules.learning.strategies.answer_upsert_strategy import (
    AnswerUpsertStrategy,
    MultipleChoiceAnswerUpsertStrategy,
    FreeTextAnswerUpsertStrategy,
    ClozeAnswerUpsertStrategy,
)
from app.modules.learning.strategies.answer_mapping_strategy import (
    AnswerMappingStrategy,
    MultipleChoiceAnswerMappingStrategy,
    FreeTextAnswerMappingStrategy,
    ClozeAnswerMappingStrategy,
)

AnswerUpsertRegistry = StrategyRegistry[AnswerTypeKey, AnswerUpsertStrategy]
AnswerMappingRegistry = StrategyRegistry[AnswerTypeKey, AnswerMappingStrategy]


def answer_upsert_registry() -> AnswerUpsertRegistry:
    return StrategyRegistry.from_strategies(
        strategies=[
            MultipleChoiceAnswerUpsertStrategy(),
            FreeTextAnswerUpsertStrategy(),
            ClozeAnswerUpsertStrategy(),
        ],
        key_getter=lambda strategy: strategy.answer_type,
    )


def answer_mapping_registry() -> AnswerMappingRegistry:
    return StrategyRegistry.from_strategies(
        strategies=[
            MultipleChoiceAnswerMappingStrategy(),
            FreeTextAnswerMappingStrategy(),
            ClozeAnswerMappingStrategy(),
        ],
        key_getter=lambda strategy: strategy.answer_type,
    )


__all__ = [
    "AnswerMappingRegistry",
    "AnswerMappingStrategy",
    "AnswerTypeKey",
    "AnswerUpsertRegistry",
    "AnswerUpsertStrategy",
    "answer_mapping_registry",
    "answer_upsert_registry",
    "normalize_answer_type",
]
