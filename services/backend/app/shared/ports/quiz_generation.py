"""Shared port definitions for quiz generation."""

from __future__ import annotations

from typing import Annotated, Protocol

from fastapi import Depends

from app.shared.quiz_generation import QuizGenerationSpec, QuizUpsertDto


class QuizGenerationPort(Protocol):
    """Port for generating quiz content via an LLM implementation."""

    async def generate_quiz(
        self,
        spec: QuizGenerationSpec,
    ) -> QuizUpsertDto:
        """Generate a quiz based on the provided specification."""


def get_quiz_generation_port() -> QuizGenerationPort:
    """Shared dependency hook for quiz generation."""
    raise NotImplementedError("QuizGenerationPort is not configured")


QuizGenerationPortDep = Annotated[
    QuizGenerationPort,
    Depends(get_quiz_generation_port),
]


__all__ = [
    "QuizGenerationPort",
    "QuizGenerationPortDep",
    "get_quiz_generation_port",
]
