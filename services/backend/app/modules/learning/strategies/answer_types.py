"""Shared types for answer strategies."""

from __future__ import annotations

from typing import Literal, cast

from app.modules.learning.models import AnswerType

AnswerTypeKey = Literal["multiple_choice", "free_text", "cloze"]


def normalize_answer_type(value: AnswerType | str) -> AnswerTypeKey:
    """Normalize an answer type enum/string to a registry key."""
    if isinstance(value, AnswerType):
        return cast(AnswerTypeKey, value.value)
    return cast(AnswerTypeKey, value)
