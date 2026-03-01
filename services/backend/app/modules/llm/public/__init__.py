"""Public LLM API for cross-module access."""

from app.modules.llm.public.services import LLMQuizGenerationService

__all__ = ["LLMQuizGenerationService"]
