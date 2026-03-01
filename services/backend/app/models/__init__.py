"""
SQLAlchemy models package.

Import Base here and all models to ensure they are registered with Alembic.
"""

from app.core.database import Base

# Import all models here so Alembic can detect them
from app.modules.auth.models import User, MagicLinkToken

# Import quiz models
from app.modules.quiz.models import (
    Quiz,
    QuizVersion,
    QuizEditSession,
    QuizOwnership,
    ShareLink,
    Task,
    MultipleChoiceTask,
    TaskMultipleChoiceOption,
    FreeTextTask,
    ClozeTask,
    TaskClozeBlank,
)

# Import learning models
from app.modules.learning.models import (
    Attempt,
    AttemptStatus,
    Answer,
    AnswerType,
    MultipleChoiceAnswer,
    AnswerMultipleChoiceSelection,
    FreeTextAnswer,
    ClozeAnswer,
    AnswerClozeItem,
)

__all__ = [
    "Base",
    # Auth models
    "User",
    "MagicLinkToken",
    # Quiz models
    "Quiz",
    "QuizVersion",
    "QuizEditSession",
    "QuizOwnership",
    "ShareLink",
    # Task models
    "Task",
    "MultipleChoiceTask",
    "TaskMultipleChoiceOption",
    "FreeTextTask",
    "ClozeTask",
    "TaskClozeBlank",
    # Learning models
    "Attempt",
    "AttemptStatus",
    # Answer models
    "Answer",
    "AnswerType",
    "MultipleChoiceAnswer",
    "AnswerMultipleChoiceSelection",
    "FreeTextAnswer",
    "ClozeAnswer",
    "AnswerClozeItem",
]
