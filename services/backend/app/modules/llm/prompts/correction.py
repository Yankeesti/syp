"""Correction prompt builder for LLM retry mechanism."""

from typing import Self

from app.shared.enums import TaskType
from app.modules.llm.prompts.constants import (
    CORRECTION_PROMPT_INTRO,
    CORRECTION_PROMPT_QUIZ_SCHEMA,
    CORRECTION_PROMPT_OUTRO,
)
from app.modules.llm.prompts.task_blocks import TASK_TYPE_SCHEMAS


class CorrectionPromptBuilder:
    """Builder for constructing correction prompts after LLM validation errors."""

    def __init__(self) -> None:
        self._parts: list[str] = []

    def with_validation_errors(self, error_str: str) -> Self:
        intro = CORRECTION_PROMPT_INTRO.format(validation_errors=error_str)
        self._parts.append(intro)
        return self

    def with_task_types(self, task_types: list[TaskType]) -> Self:

        self._parts.append(CORRECTION_PROMPT_QUIZ_SCHEMA)

        self._parts.append("TASK-TYPEN:")
        for task_type in task_types:
            schema = TASK_TYPE_SCHEMAS.get(task_type)
            if schema:
                self._parts.append(f"\n{task_type.value}:\n{schema}")

        return self

    def build(self) -> str:
        """Build the final correction prompt.

        Returns:
            The complete correction prompt string.
        """
        self._parts.append(CORRECTION_PROMPT_OUTRO)
        return "\n".join(self._parts)
