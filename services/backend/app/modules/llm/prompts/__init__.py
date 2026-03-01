"""Prompts-Modul für LLM-basierte Quiz-Generierung.

Dieses Modul enthält alle Prompt-Konstanten, Templates und den
SystemPromptBuilder für die strukturierte Prompt-Erstellung.
"""

from app.modules.llm.prompts.builder import SystemPromptBuilder
from app.modules.llm.prompts.constants import (
    # Konfiguration
    DEFAULT_NUM_QUESTIONS,
    DEFAULT_TOPIC,
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
    # Assignment
    ASSIGNMENT_SINGLE_TYPE,
    ASSIGNMENT_MULTI_INTRO,
    ASSIGNMENT_MULTI_LINE,
    ASSIGNMENT_DISTRIBUTION,
    TASK_TYPE_ASSIGNMENT_HINTS,
    # Output + Constraints
    OUTPUT_FORMAT,
    FINAL_CONSTRAINTS,
    # User Prompt Templates
    USER_PROMPT_TOPIC_TEMPLATE,
    USER_PROMPT_DOCUMENT_TEMPLATE,
    # Correction Prompt Templates
    CORRECTION_PROMPT_INTRO,
    CORRECTION_PROMPT_QUIZ_SCHEMA,
    CORRECTION_PROMPT_OUTRO,
    # Task Count Extraction
    TASK_NUMBER_EXTRACTION_PROMPT,
)
from app.modules.llm.prompts.task_blocks import (
    # Funktion
    get_task_block,
    # Legacy Blocks (für Rückwärtskompatibilität)
    TASK_TYPE_BLOCKS,
    MULTIPLE_CHOICE_BLOCK,
    FREE_TEXT_BLOCK,
    CLOZE_BLOCK,
    # Schemas
    TASK_TYPE_SCHEMAS,
    MULTIPLE_CHOICE_SCHEMA,
    FREE_TEXT_SCHEMA,
    CLOZE_SCHEMA,
)
from app.modules.llm.prompts.correction import CorrectionPromptBuilder

__all__ = [
    # Builders
    "SystemPromptBuilder",
    "CorrectionPromptBuilder",
    # Funktion
    "get_task_block",
    # Konfiguration
    "DEFAULT_NUM_QUESTIONS",
    "DEFAULT_TOPIC",
    # Rollen-Templates
    "ROLE_SINGLE",
    "ROLE_MULTI",
    "TASK_TYPE_DESCRIPTIONS",
    # Ziel-Templates
    "OBJECTIVE_FILE_ONLY",
    "OBJECTIVE_DESC_ONLY",
    "OBJECTIVE_BOTH",
    # Prozess-Templates
    "PROCESS_WITH_FILE",
    "PROCESS_DESC_ONLY",
    # Assignment-Fragmente
    "ASSIGNMENT_SINGLE_TYPE",
    "ASSIGNMENT_MULTI_INTRO",
    "ASSIGNMENT_MULTI_LINE",
    "ASSIGNMENT_DISTRIBUTION",
    "TASK_TYPE_ASSIGNMENT_HINTS",
    # Output + Constraints
    "OUTPUT_FORMAT",
    "FINAL_CONSTRAINTS",
    # User Prompt Templates
    "USER_PROMPT_TOPIC_TEMPLATE",
    "USER_PROMPT_DOCUMENT_TEMPLATE",
    # Correction Prompt Templates
    "CORRECTION_PROMPT_INTRO",
    "CORRECTION_PROMPT_QUIZ_SCHEMA",
    "CORRECTION_PROMPT_OUTRO",
    # Task Count Extraction
    "TASK_NUMBER_EXTRACTION_PROMPT",
    # Task Type Blocks (Legacy)
    "TASK_TYPE_BLOCKS",
    "MULTIPLE_CHOICE_BLOCK",
    "FREE_TEXT_BLOCK",
    "CLOZE_BLOCK",
    # Task Type Schemas
    "TASK_TYPE_SCHEMAS",
    "MULTIPLE_CHOICE_SCHEMA",
    "FREE_TEXT_SCHEMA",
    "CLOZE_SCHEMA",
]
