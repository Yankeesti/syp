"""Shared ports for cross-module communication."""

from app.shared.ports.quiz_events import (
    QuizDeletedEvent,
    QuizDeletedHandler,
    QuizEventPublisher,
    QuizEventPublisherDep,
    get_quiz_event_publisher,
)
from app.shared.ports.quiz_generation import (
    QuizGenerationPort,
    QuizGenerationPortDep,
    get_quiz_generation_port,
)
from app.shared.ports.quiz_read import (
    ClozeBlankView,
    MultipleChoiceOptionView,
    QuizAccessView,
    QuizReadPort,
    QuizReadPortDep,
    TaskDetailBaseView,
    TaskDetailClozeView,
    TaskDetailFreeTextView,
    TaskDetailMultipleChoiceView,
    TaskDetailView,
    get_quiz_read_port,
)

__all__ = [
    "ClozeBlankView",
    "MultipleChoiceOptionView",
    "QuizAccessView",
    "QuizDeletedEvent",
    "QuizDeletedHandler",
    "QuizEventPublisher",
    "QuizEventPublisherDep",
    "QuizGenerationPort",
    "QuizGenerationPortDep",
    "QuizReadPort",
    "QuizReadPortDep",
    "TaskDetailBaseView",
    "TaskDetailClozeView",
    "TaskDetailFreeTextView",
    "TaskDetailMultipleChoiceView",
    "TaskDetailView",
    "get_quiz_event_publisher",
    "get_quiz_generation_port",
    "get_quiz_read_port",
]
