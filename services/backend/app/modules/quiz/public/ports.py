"""Public quiz ports and registration for the composition root."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, FastAPI

from app.modules.quiz.events import get_quiz_event_publisher
from app.modules.quiz.dependencies import QuizServiceDep
from app.modules.quiz.public import QuizPublicService
from app.shared.ports.quiz_events import get_quiz_event_publisher as get_quiz_event_port
from app.shared.ports.quiz_read import QuizReadPort, get_quiz_read_port


def get_quiz_public_service(quiz_service: QuizServiceDep) -> QuizPublicService:
    """Factory for QuizPublicService."""
    return QuizPublicService(quiz_service)


QuizPublicServiceDep = Annotated[
    QuizPublicService,
    Depends(get_quiz_public_service),
]


def get_quiz_read_port_impl(
    quiz_public_service: QuizPublicServiceDep,
) -> QuizReadPort:
    """Adapter to expose quiz read functionality via shared port."""
    return quiz_public_service


def register_quiz_ports(app: FastAPI) -> None:
    """Register quiz implementations for shared ports."""
    app.dependency_overrides[get_quiz_read_port] = get_quiz_read_port_impl
    app.dependency_overrides[get_quiz_event_port] = get_quiz_event_publisher


__all__ = ["QuizPublicServiceDep", "register_quiz_ports"]
