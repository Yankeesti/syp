"""Answer evaluation strategies for different answer types."""

from __future__ import annotations

import re
from decimal import Decimal
from typing import Protocol

from app.shared.strategy_registry import StrategyRegistry
from app.modules.learning.models import (
    Answer,
    MultipleChoiceAnswer,
    FreeTextAnswer,
    ClozeAnswer,
)
from app.modules.learning.repositories import AnswerRepository
from app.modules.learning.strategies.answer_types import (
    AnswerTypeKey,
    normalize_answer_type,
)
from app.shared.ports.quiz_read import TaskDetailView


class AnswerEvaluationStrategy(Protocol):
    """Strategy interface for evaluating answers."""

    answer_type: AnswerTypeKey

    async def evaluate(
        self,
        answer: Answer,
        task: TaskDetailView,
        answer_repo: AnswerRepository,
    ) -> Decimal:
        """Evaluate an answer against a task and return a percentage."""


class MultipleChoiceEvaluationStrategy(AnswerEvaluationStrategy):
    """Evaluate multiple choice answers."""

    answer_type: AnswerTypeKey = "multiple_choice"

    async def evaluate(
        self,
        answer: Answer,
        task: TaskDetailView,
        answer_repo: AnswerRepository,
    ) -> Decimal:
        del answer_repo
        if not isinstance(answer, MultipleChoiceAnswer):
            return Decimal("0.0")

        if task.type != "multiple_choice":
            return Decimal("0.0")

        correct_ids = {opt.option_id for opt in task.options if opt.is_correct}
        selected_ids = {sel.option_id for sel in answer.selections}

        if correct_ids == selected_ids:
            return Decimal("100.0")
        return Decimal("0.0")


class FreeTextEvaluationStrategy(AnswerEvaluationStrategy):
    """Evaluate free text answers."""

    answer_type: AnswerTypeKey = "free_text"

    async def evaluate(
        self,
        answer: Answer,
        task: TaskDetailView,
        answer_repo: AnswerRepository,
    ) -> Decimal:
        del answer_repo
        if not isinstance(answer, FreeTextAnswer):
            return Decimal("0.0")

        if answer.percentage_correct is not None:
            return Decimal(str(answer.percentage_correct))
        return Decimal("0.0")


class ClozeEvaluationStrategy(AnswerEvaluationStrategy):
    """Evaluate cloze answers and persist item correctness."""

    answer_type: AnswerTypeKey = "cloze"

    async def evaluate(
        self,
        answer: Answer,
        task: TaskDetailView,
        answer_repo: AnswerRepository,
    ) -> Decimal:
        if not isinstance(answer, ClozeAnswer):
            return Decimal("0.0")

        if task.type != "cloze":
            return Decimal("0.0")

        if not task.blanks:
            return Decimal("100.0")

        blank_patterns = {b.blank_id: b.expected_value for b in task.blanks}
        correct_count = 0
        total_count = len(blank_patterns)

        for item in answer.items:
            expected_pattern = blank_patterns.get(item.blank_id)
            if expected_pattern:
                try:
                    is_correct = bool(
                        re.fullmatch(expected_pattern, item.provided_value),
                    )
                except re.error:
                    is_correct = expected_pattern == item.provided_value

                if is_correct:
                    correct_count += 1

                await answer_repo.set_cloze_item_correct(
                    answer.answer_id,
                    item.blank_id,
                    is_correct,
                )

        percentage = Decimal(correct_count) / Decimal(total_count) * Decimal("100.0")
        return percentage


AnswerEvaluationRegistry = StrategyRegistry[AnswerTypeKey, AnswerEvaluationStrategy]


def answer_evaluation_registry() -> AnswerEvaluationRegistry:
    """Build the evaluation strategy registry."""
    return StrategyRegistry.from_strategies(
        strategies=[
            MultipleChoiceEvaluationStrategy(),
            FreeTextEvaluationStrategy(),
            ClozeEvaluationStrategy(),
        ],
        key_getter=lambda strategy: strategy.answer_type,
    )


__all__ = [
    "AnswerEvaluationRegistry",
    "AnswerEvaluationStrategy",
    "AnswerTypeKey",
    "answer_evaluation_registry",
    "normalize_answer_type",
]
