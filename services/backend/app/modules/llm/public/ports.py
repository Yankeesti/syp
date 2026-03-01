"""Public LLM ports and registration for the composition root."""

from typing import Annotated

from fastapi import Depends, FastAPI

from app.modules.llm.dependencies import LLMServiceDep
from app.modules.llm.public.services import LLMQuizGenerationService
from app.shared.ports.quiz_generation import (
    QuizGenerationPort,
    get_quiz_generation_port,
)


def get_quiz_generation_port_impl(
    llm_service: LLMServiceDep,
) -> QuizGenerationPort:
    """Adapter to expose LLM quiz generation via shared port."""
    return LLMQuizGenerationService(llm_service)


QuizGenerationPortImplDep = Annotated[
    QuizGenerationPort,
    Depends(get_quiz_generation_port_impl),
]


def register_llm_ports(app: FastAPI) -> None:
    """Register LLM implementations for shared ports."""
    app.dependency_overrides[get_quiz_generation_port] = get_quiz_generation_port_impl


__all__ = ["QuizGenerationPortImplDep", "register_llm_ports"]
