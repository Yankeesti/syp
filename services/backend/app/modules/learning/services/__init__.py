"""Learning services package.

Use lazy imports to avoid circular import side effects.
"""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING

__all__ = ["AttemptAnswerService", "EvaluationService", "LearningCleanupService"]

if TYPE_CHECKING:
    from app.modules.learning.services.attempt_answer_service import (  # noqa: F401
        AttemptAnswerService,
    )
    from app.modules.learning.services.evaluation_service import (  # noqa: F401
        EvaluationService,
    )
    from app.modules.learning.services.cleanup_service import (  # noqa: F401
        LearningCleanupService,
    )


def __getattr__(name: str):
    if name == "AttemptAnswerService":
        module = import_module("app.modules.learning.services.attempt_answer_service")
        return module.AttemptAnswerService
    if name == "EvaluationService":
        module = import_module("app.modules.learning.services.evaluation_service")
        return module.EvaluationService
    if name == "LearningCleanupService":
        module = import_module("app.modules.learning.services.cleanup_service")
        return module.LearningCleanupService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
