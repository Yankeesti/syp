"""Builder-Pattern für System-Prompts."""

from __future__ import annotations

from typing import Self

from app.shared.enums import TaskType
from app.modules.llm.prompts.constants import (
    # Rollen
    ROLE_SINGLE,
    ROLE_MULTI,
    TASK_TYPE_DESCRIPTIONS,
    # Ziele
    OBJECTIVE_FILE_ONLY,
    OBJECTIVE_DESC_ONLY,
    OBJECTIVE_BOTH,
    # Prozess
    PROCESS_WITH_FILE,
    PROCESS_DESC_ONLY,
    # Assignment-Step
    ASSIGNMENT_SINGLE_TYPE,
    ASSIGNMENT_MULTI_INTRO,
    ASSIGNMENT_MULTI_LINE,
    ASSIGNMENT_DISTRIBUTION,
    TASK_TYPE_ASSIGNMENT_HINTS,
    # Output + Constraints
    OUTPUT_FORMAT,
    FINAL_CONSTRAINTS,
)
from app.modules.llm.prompts.task_blocks import get_task_block


class SystemPromptBuilder:
    """Builder für System-Prompts mit Fluent API.

    Ermöglicht die schrittweise Konstruktion von System-Prompts
    für die LLM-basierte Quiz-Generierung. Alle String-Templates
    werden aus constants.py importiert.

    Beispiel:
        prompt = (
            SystemPromptBuilder()
            .with_role(task_types)
            .with_objective(num_questions, has_file, has_description)
            .with_process(num_questions, task_types, has_file)
            .with_output_format()
            .with_task_schemas(task_types)
            .with_final_constraints()
            .build()
        )
    """

    def __init__(self) -> None:
        self._parts: list[str] = []

    def with_role(self, task_types: list[TaskType]) -> Self:
        """Wählt Rolle basierend auf Anzahl Task-Typen."""
        if len(task_types) == 1:
            desc = TASK_TYPE_DESCRIPTIONS[task_types[0]]
            self._parts.append(ROLE_SINGLE.format(task_type_desc=desc))
        else:
            self._parts.append(ROLE_MULTI)
        return self

    def with_objective(
        self,
        num_questions: int,
        has_file: bool,
        has_description: bool,
    ) -> Self:
        """Wählt Ziel basierend auf Kontext-Quelle."""
        if has_file and has_description:
            template = OBJECTIVE_BOTH
        elif has_file:
            template = OBJECTIVE_FILE_ONLY
        else:
            template = OBJECTIVE_DESC_ONLY

        self._parts.append(template.format(num_questions=num_questions))
        return self

    def with_process(
        self,
        num_questions: int,
        task_types: list[TaskType],
        has_file: bool,
    ) -> Self:
        """Generiert Schrittfolge mit dynamischem Assignment-Step."""
        template = PROCESS_WITH_FILE if has_file else PROCESS_DESC_ONLY
        assignment_step = self._build_assignment_step(task_types)

        self._parts.append(
            template.format(
                num_questions=num_questions,
                assignment_step=assignment_step,
            ),
        )
        return self

    def _build_assignment_step(self, task_types: list[TaskType]) -> str:
        """Baut den Assignment-Step aus Konstanten zusammen."""
        if len(task_types) == 1:
            return ASSIGNMENT_SINGLE_TYPE.format(task_type=task_types[0].value)

        lines = [ASSIGNMENT_MULTI_INTRO]
        for tt in task_types:
            desc, name = TASK_TYPE_ASSIGNMENT_HINTS[tt]
            lines.append(ASSIGNMENT_MULTI_LINE.format(description=desc, name=name))
        lines.append(
            ASSIGNMENT_DISTRIBUTION.format(
                task_types=", ".join(t.value for t in task_types),
            ),
        )
        return "\n".join(lines)

    def with_output_format(self) -> Self:
        """Fügt JSON-Schema hinzu."""
        self._parts.append(OUTPUT_FORMAT)
        return self

    def with_task_schemas(self, task_types: list[TaskType]) -> Self:
        """Fügt Task-Schemas mit angepasster Beispielanzahl ein."""
        num_types = len(task_types)
        for tt in task_types:
            block = get_task_block(tt, num_types)
            self._parts.append(block)
        return self

    def with_final_constraints(self, num_questions: int) -> Self:
        """Fügt finale Regeln hinzu."""
        self._parts.append(FINAL_CONSTRAINTS.format(num_questions=num_questions))
        return self
        return self

    def build(self) -> str:
        """Baut den finalen System-Prompt zusammen."""
        return "\n\n".join(self._parts)
