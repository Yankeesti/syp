"""Public service wrapper for LLM-based quiz generation."""

from app.modules.llm.service import LLMService
from app.shared.quiz_generation import QuizGenerationSpec, QuizUpsertDto
from app.shared.ports.quiz_generation import (
    QuizGenerationPort,
)


class LLMQuizGenerationService(QuizGenerationPort):
    """Adapter that exposes LLM quiz generation via the shared port."""

    def __init__(self, llm_service: LLMService) -> None:
        self._llm_service = llm_service

    async def generate_quiz(
        self,
        spec: QuizGenerationSpec,
    ) -> QuizUpsertDto:
        return await self._llm_service.generate_quiz(spec)
