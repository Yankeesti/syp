"""Shared enums used across modules."""

import enum


class TaskType(str, enum.Enum):
    """Task type discriminator for polymorphic inheritance."""

    MULTIPLE_CHOICE = "multiple_choice"
    FREE_TEXT = "free_text"
    CLOZE = "cloze"


__all__ = ["TaskType"]
