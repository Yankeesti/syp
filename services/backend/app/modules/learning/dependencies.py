"""Learning module dependencies for DI."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from app.shared.dependencies import DBSessionDep
from app.shared.ports.quiz_read import QuizReadPortDep
from app.modules.learning.repositories import AttemptRepository, AnswerRepository
from app.modules.learning.services import (
    AttemptAnswerService,
    EvaluationService,
    LearningCleanupService,
)
from app.modules.learning.strategies import (
    AnswerMappingRegistry,
    AnswerUpsertRegistry,
    answer_mapping_registry,
    answer_upsert_registry,
)
from app.modules.learning.services.evaluation_strategies import (
    AnswerEvaluationRegistry,
    answer_evaluation_registry,
)


@lru_cache
def get_answer_upsert_registry() -> AnswerUpsertRegistry:
    """Factory for answer upsert strategy registry."""
    return answer_upsert_registry()


@lru_cache
def get_answer_mapping_registry() -> AnswerMappingRegistry:
    """Factory for answer mapping strategy registry."""
    return answer_mapping_registry()


def get_attempt_repository(db: DBSessionDep) -> AttemptRepository:
    """Factory for AttemptRepository."""
    return AttemptRepository(db)


def get_answer_repository(db: DBSessionDep) -> AnswerRepository:
    """Factory for AnswerRepository."""
    return AnswerRepository(db)


AttemptRepositoryDep = Annotated[
    AttemptRepository,
    Depends(get_attempt_repository),
]
AnswerRepositoryDep = Annotated[
    AnswerRepository,
    Depends(get_answer_repository),
]


@lru_cache
def get_answer_evaluation_registry() -> AnswerEvaluationRegistry:
    """Factory for answer evaluation strategy registry."""
    return answer_evaluation_registry()


def get_attempt_answer_service(
    db: DBSessionDep,
    quiz_read_port: QuizReadPortDep,
    attempt_repo: AttemptRepositoryDep,
    answer_repo: AnswerRepositoryDep,
    upsert_registry: AnswerUpsertRegistry = Depends(get_answer_upsert_registry),
    mapping_registry: AnswerMappingRegistry = Depends(get_answer_mapping_registry),
) -> AttemptAnswerService:
    """Factory for AttemptAnswerService."""
    return AttemptAnswerService(
        db,
        quiz_read_port,
        upsert_registry,
        mapping_registry,
        attempt_repo,
        answer_repo,
    )


def get_evaluation_service(
    db: DBSessionDep,
    quiz_read_port: QuizReadPortDep,
    attempt_repo: AttemptRepositoryDep,
    answer_repo: AnswerRepositoryDep,
    evaluation_registry: AnswerEvaluationRegistry = Depends(
        get_answer_evaluation_registry,
    ),
) -> EvaluationService:
    """Factory for EvaluationService."""
    return EvaluationService(
        db,
        quiz_read_port,
        evaluation_registry,
        attempt_repo,
        answer_repo,
    )


def get_learning_cleanup_service(
    attempt_repo: AttemptRepositoryDep,
) -> LearningCleanupService:
    """Factory for LearningCleanupService."""
    return LearningCleanupService(attempt_repo)


AttemptAnswerServiceDep = Annotated[
    AttemptAnswerService,
    Depends(get_attempt_answer_service),
]
AnswerEvaluationRegistryDep = Annotated[
    AnswerEvaluationRegistry,
    Depends(get_answer_evaluation_registry),
]
EvaluationServiceDep = Annotated[EvaluationService, Depends(get_evaluation_service)]
LearningCleanupServiceDep = Annotated[
    LearningCleanupService,
    Depends(get_learning_cleanup_service),
]
