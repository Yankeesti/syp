"""Quiz module repositories.

This module exports all repository classes for the quiz module.
"""

from app.modules.quiz.repositories.quiz_repository import QuizRepository
from app.modules.quiz.repositories.quiz_ownership_repository import (
    QuizOwnershipRepository,
)
from app.modules.quiz.repositories.task_repository import TaskRepository
from app.modules.quiz.repositories.quiz_version_repository import (
    QuizVersionRepository,
)
from app.modules.quiz.repositories.quiz_edit_session_repository import (
    QuizEditSessionRepository,
)

__all__ = [
    "QuizRepository",
    "QuizOwnershipRepository",
    "TaskRepository",
    "QuizVersionRepository",
    "QuizEditSessionRepository",
]
